"""Blinded annotation sheets and agreement before adjudication."""
import csv
from pathlib import Path

from .data import digest, write_json, write_jsonl
from .metrics import agreement


def export_sheet(rows, output, split):
    selected = [r for r in rows if r["split"] == split]
    if not selected:
        raise ValueError("No records for annotation")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["id", "article_id", "text", "context", "labels_json", "uncertain", "note"])
        writer.writeheader()
        for r in selected:
            writer.writerow({"id": r["id"], "article_id": r["article_id"], "text": r["text"], "context": r.get("context", ""),
                             "labels_json": "", "uncertain": "", "note": ""})
    write_json(output.with_suffix(".manifest.json"), {"ids": [r["id"] for r in selected], "selected_sha256": digest(selected), "split": split})


def read_sheet(path, allowed):
    import json
    result = {}
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        for r in csv.DictReader(stream):
            if not r.get("id") or r["id"] in result:
                raise ValueError("Missing or duplicate annotation ID")
            try:
                labels = json.loads(r["labels_json"])
            except (ValueError, KeyError) as exc:
                raise ValueError(f"Complete labels_json for {r.get('id')}; use [] for none") from exc
            if not isinstance(labels, list) or any(not isinstance(x, str) for x in labels) or len(labels) != len(set(labels)) or set(labels) - set(allowed):
                raise ValueError("Invalid annotation labels")
            result[r["id"]] = labels
    return result


def compare_sheets(path_a, path_b, tax, output):
    allowed = [x["id"] for x in tax["labels"]]
    a, b = read_sheet(path_a, allowed), read_sheet(path_b, allowed)
    def targets(path):
        with Path(path).open(encoding="utf-8-sig", newline="") as stream:
            return {r["id"]: (r.get("article_id"), r.get("text"), r.get("context", "")) for r in csv.DictReader(stream)}
    if targets(path_a) != targets(path_b):
        raise ValueError("Annotation sheets must contain identical source text and context")
    result = agreement(a, b, allowed)
    write_json(output, result)
    return result


def import_sheet(path, rows, tax, split, output):
    allowed = [x["id"] for x in tax["labels"]]
    table = read_sheet(path, allowed)
    target = {r["id"] for r in rows if r["split"] == split}
    if set(table) != target:
        raise ValueError("Annotation IDs must exactly match the selected split")
    source = {r["id"]: r for r in rows}
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        for item in csv.DictReader(stream):
            original = source[item["id"]]
            if (item.get("text"), item.get("article_id"), item.get("context", "")) != (original["text"], original["article_id"], original.get("context", "")):
                raise ValueError("Annotation source text or context changed")
    result = [{**r, "labels": table[r["id"]]} if r["id"] in table else r for r in rows]
    write_jsonl(output, result)
    return {"imported": len(table), "output": str(output), "note": "Use a final adjudicated sheet here, retain independent sheets separately"}
