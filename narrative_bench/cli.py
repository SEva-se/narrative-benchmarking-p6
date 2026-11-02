from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
import time

from .annotations import compare_sheets, export_sheet, import_sheet
from .baseline import TfidfCentroid
from .data import digest, read_json, read_jsonl, source_digest, validate_dataset, write_json, write_jsonl
from .engine import execute, now
from .evaluate import evaluate


def parser():
    p = argparse.ArgumentParser(description="Narrative benchmark. Python 3.10+, no external packages.")
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("validate", "run", "baseline", "evaluate", "annotation-export", "annotation-import"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--data", required=True)
        cmd.add_argument("--taxonomy", required=True)
        if name != "validate":
            cmd.add_argument("--output" if name not in {"evaluate"} else "--run-dir", required=True)
        if name in {"run", "baseline", "annotation-export", "annotation-import"}:
            cmd.add_argument("--split", choices=["train", "dev", "test", "new", "unlabeled"], default="test")
        if name == "run":
            cmd.add_argument("--config", required=True)
            cmd.add_argument("--variant", choices=["zero", "few"], default="zero")
            cmd.add_argument("--limit", type=int)
            cmd.add_argument("--seed", type=int, default=42)
            cmd.add_argument("--execute-api", action="store_true", help="Explicitly permit real API requests")
        if name == "evaluate":
            cmd.add_argument("--bootstrap", type=int, default=500)
        if name == "annotation-import":
            cmd.add_argument("--sheet", required=True)
    cmd = sub.add_parser("agreement")
    cmd.add_argument("--a", required=True)
    cmd.add_argument("--b", required=True)
    cmd.add_argument("--taxonomy", required=True)
    cmd.add_argument("--output", required=True)
    cmd = sub.add_parser("import-csv", help="Convert a normalized CSV, not an uninspected original corpus format")
    cmd.add_argument("--input", required=True)
    cmd.add_argument("--taxonomy", required=True)
    cmd.add_argument("--output", required=True)
    cmd = sub.add_parser("compare", help="Summarize already evaluated runs; only matched inputs are comparable")
    cmd.add_argument("--runs", nargs="+", required=True)
    cmd.add_argument("--output", required=True)
    return p


def baseline(rows, tax, out, split):
    info = validate_dataset(rows, tax)
    train = [r for r in rows if r["split"] == "train"]
    dev = [r for r in rows if r["split"] == "dev"]
    selected = [r for r in rows if r["split"] == split]
    if split not in {"test", "new"} or not selected:
        raise ValueError("Baseline scores test or new splits after fitting train and tuning dev")
    model = TfidfCentroid().fit(train, [x["id"] for x in tax["labels"]])
    threshold = model.tune(dev)
    out = Path(out)
    if (out / "manifest.json").exists():
        raise ValueError("Baseline output already exists. Use a new directory")
    out.mkdir(parents=True, exist_ok=True)
    config = {"provider": "local_cpu", "model": "tfidf-centroid", "threshold": threshold,
              "threshold_selection": "dev macro-F1 over labels with positive gold support, ties prefer higher threshold"}
    manifest = {**info, "source_sha256": source_digest(), "selected_ids": [r["id"] for r in selected], "config": config, "split": split,
                "variant": "centroid", "created_utc": now(), "status": "complete",
                "interpretation": "DEMO ONLY" if info["dataset_kind"] == "synthetic_demo" else "research baseline"}
    manifest["fingerprint"] = digest(manifest)
    write_json(out / "manifest.json", manifest)
    predictions = []
    for r in selected:
        start = time.perf_counter()
        labels = model.predict(r["text"], threshold)
        predictions.append({"id": r["id"], "valid": True,
                            "prediction": {"labels": labels, "evidence": [{"label_id": k, "quote": r["text"], "explanation": "TF-IDF similarity to a positive training centroid. This full-paragraph quote needs human support review."} for k in labels]},
                            "latency_seconds": time.perf_counter() - start, "cost_usd_estimate": 0})
    write_jsonl(out / "predictions.jsonl", predictions)
    return {"output": str(out), "threshold": threshold, "records": len(selected), "latency_scope": "Prediction only; training and tuning excluded"}


def compare(runs, output):
    metrics = [read_json(Path(r) / "metrics.json") for r in runs]
    manifests = [read_json(Path(r) / "manifest.json") for r in runs]
    first = manifests[0]
    for m in manifests[1:]:
        if any(m[k] != first[k] for k in ("dataset_sha256", "taxonomy_sha256", "split")) or set(m["selected_ids"]) != set(first["selected_ids"]):
            raise ValueError("Comparison requires identical dataset, taxonomy, split and selected record IDs")
    rows = [{"run": str(r), "model": m["model"], "variant": m["variant"], "dataset_kind": m["dataset_kind"],
             "macro_f1_all_labels": m["classification"]["macro_f1_all_labels"], "micro_f1": m["classification"]["micro_f1"],
             "valid_rate": m["coverage"]["valid_rate"], "cost_usd_estimate": m["resources"]["cost_usd_estimate"],
             "median_record_seconds": m["resources"]["median_record_seconds"], "p95_record_seconds": m["resources"]["p95_record_seconds"]} for r, m in zip(runs, metrics)]
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return {"runs": len(rows), "output": str(path), "note": "Empty cost means unknown, not free. CPU and API latency have different measurement scopes."}


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "compare":
            result = compare(args.runs, args.output)
        elif args.command == "agreement":
            result = compare_sheets(args.a, args.b, read_json(args.taxonomy), args.output)
        elif args.command == "import-csv":
            with Path(args.input).open(encoding="utf-8-sig", newline="") as stream:
                rows = []
                for r in csv.DictReader(stream):
                    item = {k: r[k] for k in ("id", "article_id", "text", "split", "language", "dataset_kind")}
                    item["labels"] = json.loads(r.get("labels_json") or "null")
                    for k in ("context", "source_url", "publication_date"):
                        if r.get(k):
                            item[k] = r[k]
                    rows.append(item)
            result = validate_dataset(rows, read_json(args.taxonomy))
            write_jsonl(args.output, rows)
        else:
            rows, tax = read_jsonl(args.data), read_json(args.taxonomy)
            info = validate_dataset(rows, tax)
            if args.command == "validate":
                result = info
            elif args.command == "run":
                result = execute(rows, tax, read_json(args.config), args.output, args.split, args.variant, args.limit, args.seed, args.execute_api)
            elif args.command == "baseline":
                result = baseline(rows, tax, args.output, args.split)
            elif args.command == "evaluate":
                result = evaluate(rows, tax, args.run_dir, args.bootstrap)
            elif args.command == "annotation-export":
                export_sheet(rows, args.output, args.split)
                result = {"output": args.output, "gold_labels_exported": False}
            else:
                result = import_sheet(args.sheet, rows, tax, args.split, args.output)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
