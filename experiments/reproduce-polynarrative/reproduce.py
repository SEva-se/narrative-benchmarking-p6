"""Independent, partial PolyNarrative zero-shot reimplementation. Python 3.10+."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
import statistics
import sys
import time
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

HERE = Path(__file__).resolve().parent
VERSION = "1.0.0"


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def save(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def append(path, obj):
    with Path(path).open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def jsonl(path):
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()] if Path(path).exists() else []


def normalize(label):
    label = unicodedata.normalize("NFKC", label).casefold()
    return "".join(x for x in label if x.isalnum())


def taxonomy(path=HERE / "taxonomy_urw.json"):
    tax = load(path)
    if tax["domain"] != "URW" or not tax["fine"] or len(set(tax["fine"])) != len(tax["fine"]):
        raise ValueError("Invalid URW taxonomy")
    if len({normalize(x) for x in tax["fine"]}) != len(tax["fine"]):
        raise ValueError("Ambiguous normalized labels")
    if set(tax["parent_by_fine"]) != set(tax["fine"]) or set(tax["parent_by_fine"].values()) != set(tax["coarse"]):
        raise ValueError("Invalid taxonomy hierarchy")
    return tax


def reduce_other(labels):
    """Global Other disappears when a specific label is present; parent: Other remains."""
    values = set(labels)
    if len(values) > 1:
        values.discard("Other")
    return sorted(values)


def validate_data(data, tax):
    meta = data["metadata"]
    if meta.get("dataset_kind") not in {"synthetic_fixture", "authorized_release"}:
        raise ValueError("Declare dataset_kind as synthetic_fixture or authorized_release")
    if meta.get("domain") != "URW" or meta.get("language") != "EN":
        raise ValueError("This experiment is restricted to English URW")
    rows = data["articles"]
    if not isinstance(rows, list) or not rows:
        raise ValueError("Nonempty articles required")
    ids, texts = set(), set()
    for row in rows:
        if not isinstance(row["id"], str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", row["id"]) or row["id"] in ids:
            raise ValueError("Unsafe or duplicate article ID")
        ids.add(row["id"])
        paras = row["paragraphs"]
        if not isinstance(paras, list) or not paras or any(not isinstance(x, str) or not x.strip() for x in paras):
            raise ValueError("Nonempty explicit paragraph strings required")
        if any(re.search(r"\[paragraph_\d+:\]", x, re.I) for x in paras):
            raise ValueError("Input contains reserved paragraph tags")
        text = " ".join(" ".join(paras).casefold().split())
        if text in texts:
            raise ValueError("Duplicate article text")
        texts.add(text)
        for level in ("fine", "coarse"):
            labels = row["gold_" + level]
            if not isinstance(labels, list) or not labels or any(not isinstance(x, str) for x in labels) or len(set(labels)) != len(labels) or set(labels) - set(tax[level]):
                raise ValueError(f"Invalid {level} gold labels for {row['id']}; do not silently remap releases")
            if "Other" in labels and len(labels) > 1:
                raise ValueError("Global Other cannot coexist with specific gold labels")
        derived = reduce_other(tax["parent_by_fine"][x] for x in row["gold_fine"])
        if derived != sorted(row["gold_coarse"]):
            raise ValueError("Gold hierarchy differs from this experiment; inspect release rather than repair automatically")
    return rows


def prepare(articles, gold, ids, output, release, note, confirmed):
    """Adapter for the public three-column SemEval ST2 format, not unknown paragraph files."""
    tax = taxonomy()
    selected = [x.strip() for x in Path(ids).read_text(encoding="utf-8-sig").splitlines() if x.strip()]
    if not selected or len(selected) != len(set(selected)):
        raise ValueError("Provide a unique nonempty list of English URW article filenames")
    annotations = {}
    with Path(gold).open(encoding="utf-8-sig", newline="") as f:
        for n, fields in enumerate(csv.reader(f, delimiter="\t"), 1):
            if not fields:
                continue
            if len(fields) != 3:
                raise ValueError(f"Gold line {n}: expected exactly three tab-separated fields, no header")
            aid, coarse, fine = fields
            if aid in annotations:
                raise ValueError("Duplicate gold article ID")
            annotations[aid] = ([x.strip() for x in coarse.split(";")], [x.strip() for x in fine.split(";")])
    base = Path(articles).resolve()
    rows, hashes = [], {}
    for aid in selected:
        if not re.fullmatch(r"EN_[A-Za-z0-9_.-]+\.txt", aid):
            raise ValueError("IDs must be explicit English article basenames, e.g. EN_10001.txt")
        source = (base / aid).resolve()
        if source.parent != base or aid not in annotations:
            raise ValueError("Missing gold or unsafe article path")
        text = source.read_text(encoding="utf-8-sig")
        # Keep the title as a paragraph; paragraph boundary rule is an explicit deviation.
        paras = [x.strip() for x in re.split(r"\n\s*\n", text.replace("\r\n", "\n")) if x.strip()]
        coarse, fine = annotations[aid]
        rows.append({"id": aid, "paragraphs": paras, "gold_coarse": coarse, "gold_fine": fine})
        hashes[aid] = file_hash(source)
    data = {"metadata": {"dataset_kind": "authorized_release", "domain": "URW", "language": "EN",
            "release_name": release, "release_note": note, "paper_test_mapping_confirmed": confirmed,
            "split": "paper_test" if confirmed else "unverified_release",
            "source_gold_sha256": file_hash(gold), "source_ids_sha256": file_hash(ids),
            "source_article_sha256": hashes,
            "segmentation": "blank-line-separated blocks, title retained; not verified original paragraph boundaries",
            "selection": "explicit IDs; establish domain from approved metadata or human review, not model outcomes"},
            "articles": rows}
    validate_data(data, tax)
    if Path(output).exists():
        raise ValueError("Output exists; choose a new prepared dataset path")
    save(output, data)
    return {"articles": len(rows), "output": str(output), "paper_test_mapping_confirmed": confirmed}


def make_request(row, tax, cfg):
    prompt = (HERE / "prompt_c1.txt").read_text(encoding="utf-8").replace("{codebook_urw}", "\n".join(tax["fine"]))
    text = "\n\n".join(f"[paragraph_{n}:]\n{p}" for n, p in enumerate(row["paragraphs"], 1))
    return {"model": cfg["model"], "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": text}],
            **cfg["parameters"]}


def parse_output(raw, count, tax):
    """Conservative documented normalization; never semantic/fuzzy-match labels."""
    index = {normalize(x): x for x in tax["fine"]}
    parsed, unknown, issues = {}, [], []
    if not isinstance(raw, str):
        return {"valid": False, "fine": [], "coarse": [], "paragraphs": {}, "unknown_labels": [], "issues": ["no_text"]}
    clean = raw.strip()
    if clean.startswith("```"):
        clean = re.sub(r"^```[^\n]*\n|\n```$", "", clean)
    tags = list(re.finditer(r"\[paragraph_(\d+):\]", clean, re.I))
    if not tags:
        issues.append("no_paragraph_tags")
    elif clean[:tags[0].start()].strip():
        issues.append("unexpected_preamble")
    for i, match in enumerate(tags):
        pid = int(match.group(1))
        chunk = clean[match.end():tags[i+1].start() if i + 1 < len(tags) else len(clean)].strip()
        if pid < 1 or pid > count:
            issues.append("out_of_range_paragraph")
            continue
        if pid in parsed:
            issues.append("duplicate_paragraph")
            continue
        accepted = []
        for part in chunk.split(";"):
            part = part.strip().strip("*` \t\n")
            label = index.get(normalize(part))
            if label is None:
                unknown.append({"paragraph": pid, "text": part})
            else:
                accepted.append(label)
        if not accepted:
            issues.append("paragraph_without_recognized_label")
        if "Other" in accepted and len(set(accepted)) > 1:
            issues.append("other_with_specific_label")
        parsed[pid] = reduce_other(accepted)
    if set(parsed) != set(range(1, count + 1)):
        issues.append("missing_paragraphs")
    if unknown:
        issues.append("unrecognized_labels")
    fine = reduce_other(x for labels in parsed.values() for x in labels)
    coarse = reduce_other(tax["parent_by_fine"][x] for x in fine)
    return {"valid": not issues, "fine": fine, "coarse": coarse, "paragraphs": parsed,
            "unknown_labels": unknown, "issues": sorted(set(issues))}


def metrics(gold, predicted, labels):
    if not gold or len(gold) != len(predicted):
        raise ValueError("Equal nonempty metric inputs required")
    by_label, totals = {}, [0, 0, 0]
    for label in labels:
        tp = sum(label in g and label in p for g, p in zip(gold, predicted))
        fp = sum(label not in g and label in p for g, p in zip(gold, predicted))
        fn = sum(label in g and label not in p for g, p in zip(gold, predicted))
        by_label[label] = {"support": tp + fn, "predicted": tp + fp, "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0}
        totals = [a + b for a, b in zip(totals, (tp, fp, fn))]
    active = [x["f1"] for x in by_label.values() if x["support"] or x["predicted"]]
    tp, fp, fn = totals
    return {"n": len(gold), "macro_f1_fixed_inventory": statistics.mean(x["f1"] for x in by_label.values()),
            "macro_f1_observed_union": statistics.mean(active) if active else 0.0,
            "sample_f1": statistics.mean(2 * len(set(g) & set(p)) / (len(set(g)) + len(set(p))) if g or p else 0.0 for g, p in zip(gold, predicted)),
            "micro_f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0,
            "exact_match": statistics.mean(set(g) == set(p) for g, p in zip(gold, predicted)), "by_label": by_label}


def validate_config(cfg):
    if set(cfg) - {"model", "endpoint", "api_key_env", "parameters", "timeout_seconds", "max_input_chars", "max_api_calls", "pricing_usd_per_million", "allow_local_http"}:
        raise ValueError("Unknown config field; never put secrets in config")
    if not isinstance(cfg.get("model"), str) or not cfg["model"].strip() or cfg["model"].startswith("REPLACE"):
        raise ValueError("Set an exact provider model ID")
    u = urlparse(cfg["endpoint"])
    local = u.scheme == "http" and u.hostname in {"127.0.0.1", "localhost"} and cfg.get("allow_local_http") is True
    if (u.scheme != "https" and not local) or not u.netloc or u.username or u.password or u.query or u.fragment:
        raise ValueError("Use a full HTTPS chat-completions endpoint without credentials or query")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", cfg["api_key_env"]):
        raise ValueError("Set an environment-variable name for the API key")
    for key in ("max_input_chars", "max_api_calls"):
        if type(cfg.get(key)) is not int or cfg[key] < 1:
            raise ValueError(f"Positive {key} required")
    timeout = cfg.get("timeout_seconds", 120)
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("Positive timeout required")
    params = cfg["parameters"]
    if set(params) - {"temperature", "top_p", "max_tokens", "max_completion_tokens", "seed"}:
        raise ValueError("Unsupported parameter; response-format changes would alter this experiment")
    caps = [params[x] for x in ("max_tokens", "max_completion_tokens") if x in params]
    if len(caps) != 1 or type(caps[0]) is not int or caps[0] < 1:
        raise ValueError("One positive output-token cap required")
    for key, maximum in (("temperature", 2), ("top_p", 1)):
        if key in params and (type(params[key]) not in (int, float) or not math.isfinite(params[key]) or not 0 <= params[key] <= maximum):
            raise ValueError("Invalid sampling parameter")
    if "seed" in params and type(params["seed"]) is not int:
        raise ValueError("Seed must be an integer")
    for key, value in cfg.get("pricing_usd_per_million", {}).items():
        if key not in {"input", "output", "cached_input"} or (value is not None and (type(value) not in (int, float) or not math.isfinite(value) or value < 0)):
            raise ValueError("Invalid price")


def cost(usage, pricing):
    if not isinstance(usage, dict):
        return None
    inp, out = usage.get("prompt_tokens"), usage.get("completion_tokens")
    details = usage.get("prompt_tokens_details") or {}
    if not isinstance(details, dict):
        return None
    cached = details.get("cached_tokens", 0)
    if any(type(x) is not int or x < 0 for x in (inp, out, cached)) or cached > inp:
        return None
    if any(pricing.get(x) is None for x in ("input", "output")) or (cached and pricing.get("cached_input") is None):
        return None
    return ((inp - cached) * pricing["input"] + cached * (pricing.get("cached_input") or 0) + out * pricing["output"]) / 1e6


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def complete(cfg, payload):
    key = os.environ.get(cfg["api_key_env"])
    if not key:
        raise ValueError("API key environment variable is empty")
    req = Request(cfg["endpoint"], data=json.dumps(payload).encode(), method="POST",
                  headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    with build_opener(NoRedirect()).open(req, timeout=cfg.get("timeout_seconds", 120)) as response:
        body = response.read(5_000_001)
        if len(body) > 5_000_000:
            raise ValueError("Provider response exceeds 5 MB")
        return json.loads(body)


def plan(data, cfg, limit=None):
    tax = taxonomy()
    rows = validate_data(data, tax)
    validate_config(cfg)
    if limit is not None and limit < 1:
        raise ValueError("Positive limit required")
    rows = sorted(rows, key=lambda x: x["id"])[:limit]
    requests = [make_request(row, tax, cfg) for row in rows]
    for request in requests:
        if sum(len(x["content"]) for x in request["messages"]) > cfg["max_input_chars"]:
            raise ValueError("Input exceeds character cap; do not silently truncate or chunk")
    identity = {"version": VERSION, "source_sha256": file_hash(__file__), "prompt_sha256": file_hash(HERE / "prompt_c1.txt"),
                "taxonomy_sha256": digest(tax), "dataset_sha256": digest(data), "config": cfg,
                "selected_ids": [r["id"] for r in rows], "request_sha256": [digest(x) for x in requests]}
    return rows, requests, identity


def run(data, cfg, output, limit=None, execute=False):
    if not execute:
        raise ValueError("API execution requires --execute-api; preview is offline")
    rows, requests, identity = plan(data, cfg, limit)
    if data["metadata"]["dataset_kind"] != "authorized_release":
        raise ValueError("Synthetic fixtures cannot be used as real model experiments")
    if not data["metadata"].get("paper_test_mapping_confirmed"):
        raise ValueError("Verify and confirm the paper TEST/shared-task dev mapping before API execution")
    if not os.environ.get(cfg["api_key_env"]):
        raise ValueError(f"Set {cfg['api_key_env']} in the local environment")
    folder = Path(output)
    folder.mkdir(parents=True, exist_ok=True)
    lock = folder / ".run.lock"
    # Acquire before modifying any run artifact. A stale lock requires manual inspection.
    with lock.open("x"):
        pass
    try:
        mp, pp, ep = folder / "manifest.json", folder / "predictions.jsonl", folder / "attempts.jsonl"
        fp = digest(identity)
        if mp.exists():
            if load(mp)["fingerprint"] != fp:
                raise ValueError("Immutable run changed; choose a new output directory")
        else:
            if pp.exists() or ep.exists():
                raise ValueError("Run artifacts exist without a manifest")
            save(mp, {"identity": identity, "fingerprint": fp, "metadata": data["metadata"], "status": "started"})
        old, events = jsonl(pp), jsonl(ep)
        done = {x["id"] for x in old}
        if len(done) != len(old) or done - set(identity["selected_ids"]):
            raise ValueError("Invalid prior prediction IDs")
        if {x["id"] for x in events if x["event"] == "started"} - done:
            raise ValueError("Unresolved attempt: inspect ledger and billing before recovery; no automatic replay")
        calls = sum(x["event"] == "started" for x in events)
        for row, payload in zip(rows, requests):
            if row["id"] in done:
                continue
            if calls >= cfg["max_api_calls"]:
                break
            calls += 1
            append(ep, {"event": "started", "id": row["id"], "request_sha256": digest(payload), "utc_unix": time.time()})
            result = {"id": row["id"], "valid": False, "fine": [], "coarse": [], "cost_usd_estimate": None}
            start = time.perf_counter()
            try:
                response = complete(cfg, payload)
                # Persist complete response before parsing to retain usage and malformed outputs.
                save(folder / "responses" / (row["id"] + ".json"), response)
                result.update(usage=response.get("usage"), resolved_model=response.get("model"), response_id=response.get("id"))
                result["cost_usd_estimate"] = cost(response.get("usage"), cfg.get("pricing_usd_per_million", {}))
                choice = response["choices"][0]
                raw = choice["message"].get("content")
                result.update(parse_output(raw, len(row["paragraphs"]), taxonomy()))
                result.update(raw_output=raw, finish_reason=choice.get("finish_reason"))
                if choice.get("finish_reason") != "stop":
                    result["valid"] = False
                    result["issues"].append("non_stop_finish_reason")
            except HTTPError as exc:
                result["issues"] = [f"http_{exc.code}"]
            except (URLError, TimeoutError, OSError, ValueError, KeyError, IndexError, TypeError):
                result["issues"] = ["transport_or_protocol_error"]
            result["latency_seconds"] = time.perf_counter() - start
            append(pp, result)
            append(ep, {"event": "finished", "id": row["id"], "valid": result["valid"], "utc_unix": time.time()})
            done.add(row["id"])
        manifest = load(mp)
        manifest.update(status="complete" if len(done) == len(rows) else "request_cap_reached", completed=len(done), calls=calls)
        save(mp, manifest)
        return {"status": manifest["status"], "completed": len(done), "selected": len(rows), "api_calls": calls}
    finally:
        lock.unlink()


def evaluate(data, predictions, output):
    tax = taxonomy()
    rows = validate_data(data, tax)
    by_id = {x["id"]: x for x in predictions}
    if len(by_id) != len(predictions) or set(by_id) - {x["id"] for x in rows}:
        raise ValueError("Duplicate or unknown prediction IDs")
    for p in predictions:
        if type(p.get("valid")) is not bool or any(not isinstance(p.get(level), list) or set(p[level]) - set(tax[level]) for level in ("fine", "coarse")):
            raise ValueError("Invalid parsed predictions")
    report = {"status": "synthetic_fixture_only" if data["metadata"]["dataset_kind"] == "synthetic_fixture" else "partial_reimplementation_results",
              "metadata": data["metadata"], "dataset_sha256": digest(data), "selected_articles": len(rows),
              "missing_articles": sum(r["id"] not in by_id for r in rows),
              "invalid_articles": sum(not p["valid"] for p in predictions),
              "comparison_warning": "English URW only, paragraph-to-document union; no direct delta against multilingual Table 4. Not official scorer parity."}
    for level in ("fine", "coarse"):
        gold = [r["gold_" + level] for r in rows]
        strict = [by_id[r["id"]][level] if r["id"] in by_id and by_id[r["id"]]["valid"] else [] for r in rows]
        filtered = [by_id.get(r["id"], {}).get(level, []) for r in rows]
        report[level] = {"strict_format": metrics(gold, strict, tax[level]), "filtered_diagnostic": metrics(gold, filtered, tax[level])}
    costs = [p.get("cost_usd_estimate") for p in predictions]
    report["resource_summary"] = {"known_cost_usd_lower_bound": sum(x for x in costs if x is not None),
        "total_cost_usd_estimate": sum(costs) if len(predictions) == len(rows) and all(x is not None for x in costs) else None,
        "mean_observed_latency_seconds": statistics.mean(p["latency_seconds"] for p in predictions) if predictions and all("latency_seconds" in p for p in predictions) else None,
        "energy_measured": False}
    save(output, report)
    return {k: report[k] for k in ("status", "selected_articles", "missing_articles", "invalid_articles")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("prepare", help="Import authorized three-column ST2 document gold")
    for flag in ("articles", "gold", "ids", "output", "release", "note"):
        p.add_argument("--" + flag, required=True)
    p.add_argument("--confirm-paper-test", action="store_true")
    for name in ("validate", "preview", "run", "evaluate"):
        p = commands.add_parser(name)
        p.add_argument("--data", required=True)
        if name in {"preview", "run"}:
            p.add_argument("--config", required=True)
            p.add_argument("--limit", type=int)
            p.add_argument("--output", required=True)
        if name == "run":
            p.add_argument("--execute-api", action="store_true")
        if name == "evaluate":
            p.add_argument("--run-dir", required=True)
            p.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            result = prepare(args.articles, args.gold, args.ids, args.output, args.release, args.note, args.confirm_paper_test)
        else:
            data = load(args.data)
            rows = validate_data(data, taxonomy())
            if args.command == "validate":
                result = {"articles": len(rows), "metadata": data["metadata"], "dataset_sha256": digest(data)}
            elif args.command == "evaluate":
                folder = Path(args.run_dir)
                manifest = load(folder / "manifest.json")
                if manifest["identity"]["dataset_sha256"] != digest(data):
                    raise ValueError("Evaluation dataset differs from run dataset")
                ids = set(manifest["identity"]["selected_ids"])
                selected = {"metadata": data["metadata"], "articles": [r for r in rows if r["id"] in ids]}
                if len(selected["articles"]) != len(ids):
                    raise ValueError("Run selection mismatch")
                result = evaluate(selected, jsonl(folder / "predictions.jsonl"), args.output)
            else:
                cfg = load(args.config)
                if args.command == "run":
                    result = run(data, cfg, args.output, args.limit, args.execute_api)
                else:
                    selected, requests, identity = plan(data, cfg, args.limit)
                    save(args.output, {"identity": identity, "requests": requests,
                         "note": "Offline preview, not an experiment. Contains source texts; keep private."})
                    result = {"articles": len(selected), "api_calls": 0, "output": args.output,
                              "warning": "A character cap is not a token/context-window guarantee. Check the selected deployment."}
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, KeyError, OSError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
