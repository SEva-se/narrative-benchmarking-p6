"""Sequential HTTP runner with durable attempt ledger and immutable run fingerprints."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import platform
import random
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from . import __version__
from .data import append_jsonl, digest, read_json, read_jsonl, source_digest, validate_dataset, validate_prediction, write_json
from .prompts import PROMPT_VERSION, messages


def now():
    return datetime.now(timezone.utc).isoformat()


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def validate_config(cfg):
    if cfg.get("provider") not in {"demo", "chat_completions"}:
        raise ValueError("provider must be demo or chat_completions")
    if not isinstance(cfg.get("model"), str) or not cfg["model"].strip():
        raise ValueError("A model ID is required")
    if any(k in cfg for k in ("api_key", "token", "authorization", "headers")):
        raise ValueError("Secrets and headers do not belong in config; use api_key_env")
    for k, default in (("max_api_calls", 20), ("max_attempts_per_record", 2), ("max_input_chars", 40000)):
        v = cfg.get(k, default)
        if not isinstance(v, int) or isinstance(v, bool) or v < 1:
            raise ValueError(f"{k} must be a positive integer")
    for key in ("timeout_seconds", "delay_seconds"):
        value = cfg.get(key, 60 if key == "timeout_seconds" else 0)
        if not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0 or (key == "timeout_seconds" and value == 0):
            raise ValueError(f"Invalid {key}")
    params = cfg.get("parameters", {})
    if not isinstance(params, dict) or set(params) - {"temperature", "max_tokens", "max_completion_tokens", "response_format", "reasoning_effort", "seed", "top_p"}:
        raise ValueError("Unsupported request parameter")
    if "max_tokens" in params and "max_completion_tokens" in params:
        raise ValueError("Use one output-token limit parameter")
    if cfg["provider"] == "chat_completions":
        if cfg["model"].startswith("REPLACE_"):
            raise ValueError("Replace the example model ID with an available provider model")
        cap = params.get("max_completion_tokens", params.get("max_tokens"))
        if not isinstance(cap, int) or isinstance(cap, bool) or cap < 1:
            raise ValueError("Live requests require an explicit positive output-token cap")
        u = urlparse(cfg.get("endpoint", ""))
        local = u.scheme == "http" and u.hostname in {"localhost", "127.0.0.1"} and cfg.get("allow_local_http") is True
        if (u.scheme != "https" and not local) or not u.netloc or u.username or u.password or u.query or u.fragment:
            raise ValueError("Use a full HTTPS endpoint without credentials, query or fragment")
        if not cfg.get("api_key_env"):
            raise ValueError("api_key_env is required")
    prices = cfg.get("pricing_usd_per_million", {})
    if set(prices) - {"input", "output", "cached_input"}:
        raise ValueError("Unknown pricing field")
    for v in prices.values():
        if v is not None and (not isinstance(v, (int, float)) or isinstance(v, bool) or v < 0 or not math.isfinite(v)):
            raise ValueError("Price must be nonnegative finite number or null")


def calculated_cost(usage, pricing):
    """A list-price estimate. Missing usage or cache rates stays unknown, never zero."""
    if not isinstance(usage, dict) or not isinstance(pricing, dict):
        return None
    inp, out = usage.get("prompt_tokens"), usage.get("completion_tokens")
    cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens", 0)
    values = [inp, out, cached]
    if any(not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v) or v < 0 for v in values) or cached > inp:
        return None
    if pricing.get("input") is None or pricing.get("output") is None or (cached and pricing.get("cached_input") is None):
        return None
    return ((inp - cached) * pricing["input"] + cached * (pricing.get("cached_input") or 0) + out * pricing["output"]) / 1_000_000


def demo_response(text, labels):
    """Fixed lexical teaching fixture. It never reads gold labels and is not an LLM."""
    patterns = {"CC_POLICY": r"tax|policy|policies|bills", "CC_SCIENCE": r"scientist|science|measurements",
                "CC_DOWNPLAY": r"natural cycle|exaggerat|not serious", "CC_TECH": r"wind turbine|solar panel|renewable"}
    chosen = [k for k in sorted(patterns) if k in labels and re.search(patterns[k], text, re.I)]
    obj = {"labels": chosen, "evidence": [{"label_id": k, "quote": text,
            "explanation": "Synthetic lexical fixture selected a keyword. Human semantic review is required."} for k in chosen]}
    return json.dumps(obj), {}, "demo-keyword-fixture"


def http_complete(cfg, payload):
    key = os.environ.get(cfg["api_key_env"], "")
    if not key:
        raise ValueError(f"Set environment variable {cfg['api_key_env']} locally")
    request = Request(cfg["endpoint"], data=json.dumps(payload).encode(), headers={
        "Content-Type": "application/json", "Authorization": "Bearer " + key}, method="POST")
    with build_opener(NoRedirect()).open(request, timeout=cfg.get("timeout_seconds", 60)) as response:
        # Bound malformed server responses to avoid unbounded memory consumption.
        data = response.read(5_000_001)
        if len(data) > 5_000_000:
            raise ValueError("Provider response exceeds 5 MB")
        return json.loads(data)


def execute(rows, tax, cfg, output, split="test", variant="zero", limit=None, seed=42, live=False):
    info = validate_dataset(rows, tax)
    validate_config(cfg)
    if cfg["provider"] != "demo" and not live:
        raise ValueError("Live execution requires --execute-api")
    if cfg["provider"] == "demo" and info["dataset_kind"] != "synthetic_demo":
        raise ValueError("Demo fixture can only run synthetic_demo data")
    selected = [r for r in rows if r["split"] == split]
    random.Random(seed).shuffle(selected)
    if limit is not None:
        if limit < 1:
            raise ValueError("limit must be positive")
        selected = selected[:limit]
    if not selected:
        raise ValueError(f"No records for split {split}")
    example_ids = cfg.get("example_ids", []) if variant == "few" else []
    index = {r["id"]: r for r in rows}
    if len(example_ids) != len(set(example_ids)) or any(i not in index for i in example_ids):
        raise ValueError("Unknown or duplicate few-shot example IDs")
    examples = [index[i] for i in example_ids]
    allowed = {x["id"] for x in tax["labels"]}
    for e in examples:
        if e["split"] != "train":
            raise ValueError("Few-shot example outside train split")
        validate_prediction({"labels": e["labels"], "evidence": e.get("evidence")}, e["text"], allowed)
    requests = []
    for r in selected:
        msg = messages(r, tax, variant, examples)
        if sum(len(x["content"]) for x in msg) > cfg.get("max_input_chars", 40000):
            raise ValueError(f"Input too long at {r['id']}; no silent truncation")
        requests.append((r, {"model": cfg["model"], "messages": msg, **cfg.get("parameters", {})}))
    identity = {**info, "software_version": __version__, "source_sha256": source_digest(), "prompt_version": PROMPT_VERSION,
                "config": cfg, "split": split, "variant": variant, "seed": seed,
                "selected_ids": [r["id"] for r in selected], "request_hashes": [digest(p) for _, p in requests]}
    fingerprint = digest(identity)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    lock = output / ".run.lock"
    try:
        handle = lock.open("x")
    except FileExistsError as exc:
        raise ValueError("Run directory is locked. Inspect a previous process before removing a stale .run.lock") from exc
    try:
        handle.close()
        manifest_path = output / "manifest.json"
        if manifest_path.exists():
            if read_json(manifest_path).get("fingerprint") != fingerprint:
                raise ValueError("Run fingerprint changed. Choose a new output directory")
        else:
            if (output / "predictions.jsonl").exists() or (output / "attempts.jsonl").exists():
                raise ValueError("Run files without manifest; use an empty directory")
            write_json(manifest_path, {**identity, "fingerprint": fingerprint, "created_utc": now(),
                                     "python": platform.python_version(), "status": "started",
                                     "interpretation": "DEMO ONLY" if info["dataset_kind"] == "synthetic_demo" else "research run"})
        predictions_path, attempts_path = output / "predictions.jsonl", output / "attempts.jsonl"
        previous = read_jsonl(predictions_path) if predictions_path.exists() else []
        if len({r["id"] for r in previous}) != len(previous):
            raise ValueError("Duplicate prediction IDs in existing run")
        done = {r["id"] for r in previous}
        events = read_jsonl(attempts_path) if attempts_path.exists() else []
        unresolved = {e["id"] for e in events if e["event"] == "started"} - done
        if unresolved:
            raise ValueError("Uncommitted prior attempts exist. Inspect the ledger and billing before creating a separate recovery run")
        calls = sum(e["event"] == "started" for e in events)
        status = "complete"
        for row, payload in requests:
            if row["id"] in done:
                continue
            if cfg["provider"] != "demo" and not os.environ.get(cfg["api_key_env"]):
                raise ValueError(f"Set environment variable {cfg['api_key_env']} locally")
            if calls >= cfg.get("max_api_calls", 20):
                status = "request_limit_reached"
                break
            started = time.perf_counter()
            final = {"id": row["id"], "article_id": row["article_id"], "valid": False, "prediction": None,
                     "usage": None, "cost_usd_estimate": None, "cost_complete": True, "attempt_count": 0,
                     "request_sha256": digest(payload), "completed_utc": None}
            total_cost, all_cost_known = 0.0, True
            for attempt in range(1, cfg.get("max_attempts_per_record", 2) + 1):
                if calls >= cfg.get("max_api_calls", 20):
                    break
                calls += 1
                final["attempt_count"] += 1
                event_id = f"{row['id']}:{calls}"
                append_jsonl(attempts_path, {"event": "started", "event_id": event_id, "id": row["id"], "utc": now(), "request_sha256": digest(payload)})
                attempt_start = time.perf_counter()
                try:
                    if cfg["provider"] == "demo":
                        raw, usage, resolved_model = demo_response(row["text"], allowed)
                        finish_reason, response_id = "stop", None
                        usage_cost = 0.0
                    else:
                        response = http_complete(cfg, payload)
                        usage = response.get("usage")
                        usage_cost = calculated_cost(usage, cfg.get("pricing_usd_per_million"))
                        # Persist usage before parsing content, so invalid JSON is still accounted for.
                        append_jsonl(attempts_path, {"event": "response", "event_id": event_id, "id": row["id"],
                                     "usage": usage, "cost_usd_estimate": usage_cost, "response_id": response.get("id"), "utc": now()})
                        choice = response["choices"][0]
                        raw = choice["message"].get("content")
                        resolved_model, response_id = response.get("model"), response.get("id")
                        finish_reason = choice.get("finish_reason")
                    all_cost_known &= usage_cost is not None
                    total_cost += usage_cost or 0.0
                    final.update(raw_output=raw, usage=usage, resolved_model=resolved_model, response_id=response_id, finish_reason=finish_reason)
                    error = None
                    try:
                        if finish_reason not in {"stop", None}:
                            raise ValueError(f"Incomplete response: {finish_reason}")
                        if not isinstance(raw, str):
                            raise ValueError("No string content, possible refusal")
                        obj = json.loads(raw)
                        final["prediction"] = validate_prediction(obj, row["text"], allowed)
                        final["valid"] = True
                    except (ValueError, TypeError) as exc:
                        error = str(exc)
                    final["error"] = error
                    append_jsonl(attempts_path, {"event": "finished", "event_id": event_id, "id": row["id"],
                                 "status": "valid" if final["valid"] else "invalid_output", "utc": now(),
                                 "latency_seconds": time.perf_counter() - attempt_start})
                    # Invalid model outputs are benchmark outcomes, never silently retried.
                    break
                except HTTPError as exc:
                    all_cost_known = False
                    final["error"] = f"HTTP {exc.code}"
                    append_jsonl(attempts_path, {"event": "finished", "event_id": event_id, "id": row["id"],
                                 "status": final["error"], "cost_unknown": True, "utc": now(),
                                 "latency_seconds": time.perf_counter() - attempt_start})
                    if exc.code not in {429, 500, 502, 503, 504} or attempt == cfg.get("max_attempts_per_record", 2):
                        break
                    time.sleep(min(2 ** (attempt - 1), 4))
                except (URLError, TimeoutError, OSError, ValueError, KeyError, IndexError, TypeError) as exc:
                    all_cost_known = False
                    final["error"] = f"Transport/protocol error: {type(exc).__name__}"
                    append_jsonl(attempts_path, {"event": "finished", "event_id": event_id, "id": row["id"],
                                 "status": final["error"], "cost_unknown": True, "utc": now(),
                                 "latency_seconds": time.perf_counter() - attempt_start})
                    # A timeout can already have incurred charges. Do not automatically replay it.
                    break
            final.update(latency_seconds=time.perf_counter() - started, cost_usd_estimate=total_cost if all_cost_known else None,
                         known_cost_usd_lower_bound=total_cost, cost_complete=all_cost_known, completed_utc=now())
            append_jsonl(predictions_path, final)
            done.add(row["id"])
            delay = cfg.get("delay_seconds", 0)
            if delay:
                time.sleep(delay)
        manifest = read_json(manifest_path)
        manifest.update(status=status, updated_utc=now(), finished_records=len(done), api_attempts=calls)
        write_json(manifest_path, manifest)
        return {"status": status, "finished_records": len(done), "selected_records": len(selected), "api_attempts": calls, "output": str(output)}
    finally:
        lock.unlink(missing_ok=True)
