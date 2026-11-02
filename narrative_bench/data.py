"""Strict JSONL contracts and split leakage checks. No third-party dependencies."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def read_jsonl(path):
    result = []
    for number, line in enumerate(Path(path).read_text(encoding="utf-8-sig").splitlines(), 1):
        if line.strip():
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at {path}:{number}") from exc
            if not isinstance(item, dict):
                raise ValueError(f"Object expected at {path}:{number}")
            result.append(item)
    return result


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def write_jsonl(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(x, ensure_ascii=False, allow_nan=False) + "\n" for x in rows), encoding="utf-8")


def append_jsonl(path, obj):
    with Path(path).open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(obj, ensure_ascii=False, allow_nan=False) + "\n")
        stream.flush()


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def source_digest():
    return digest({p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(__file__).parent.glob("*.py"))})


def normalized(text):
    return re.sub(r"\s+", " ", text.casefold()).strip()


def validate_taxonomy(tax):
    if not isinstance(tax.get("version"), str) or not tax["version"]:
        raise ValueError("Taxonomy requires a version")
    labels = tax.get("labels")
    if not isinstance(labels, list) or not labels:
        raise ValueError("Taxonomy requires a non-empty labels list")
    ids = []
    for entry in labels:
        if not all(isinstance(entry.get(k), str) and entry[k].strip() for k in ("id", "name", "definition")):
            raise ValueError("Each label requires string id, name and definition")
        ids.append(entry["id"])
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate taxonomy label id")
    return set(ids)


def validate_dataset(rows, tax):
    allowed = validate_taxonomy(tax)
    if not rows:
        raise ValueError("Empty dataset")
    ids, articles, texts = set(), {}, {}
    counts = {}
    for row in rows:
        for key in ("id", "article_id", "text", "split", "language", "dataset_kind"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise ValueError(f"Missing nonempty string {key}: {row.get('id')}")
        if row["split"] not in {"train", "dev", "test", "new", "unlabeled"}:
            raise ValueError(f"Unknown split: {row['split']}")
        if row["dataset_kind"] not in {"synthetic_demo", "research"}:
            raise ValueError("dataset_kind must be synthetic_demo or research")
        if row["id"] in ids:
            raise ValueError(f"Duplicate id: {row['id']}")
        ids.add(row["id"])
        labels = row.get("labels")
        if labels is not None:
            if not isinstance(labels, list) or any(not isinstance(x, str) for x in labels):
                raise ValueError(f"labels must be a string list or null: {row['id']}")
            if len(labels) != len(set(labels)) or set(labels) - allowed:
                raise ValueError(f"Duplicate or unknown gold labels: {row['id']}")
        for key, mapping in ((row["article_id"], articles), (normalized(row["text"]), texts)):
            previous = mapping.setdefault(key, row["split"])
            if previous != row["split"]:
                raise ValueError(f"Cross-split article/text leakage at {row['id']}")
        counts[row["split"]] = counts.get(row["split"], 0) + 1
    kinds = {x["dataset_kind"] for x in rows}
    if len(kinds) != 1:
        raise ValueError("Do not mix synthetic_demo and research records")
    return {"records": len(rows), "articles": len(articles), "splits": counts,
            "dataset_kind": next(iter(kinds)), "dataset_sha256": digest(rows), "taxonomy_sha256": digest(tax)}


def validate_prediction(obj, text, allowed):
    """Reject a complete response if its schema or any source quote is invalid."""
    if not isinstance(obj, dict) or set(obj) != {"labels", "evidence"}:
        raise ValueError("Response must contain exactly labels and evidence")
    labels, evidence = obj["labels"], obj["evidence"]
    if not isinstance(labels, list) or any(not isinstance(x, str) for x in labels):
        raise ValueError("labels must be a list of strings")
    if len(labels) != len(set(labels)) or set(labels) - set(allowed):
        raise ValueError("Unknown or duplicate predicted labels")
    if not isinstance(evidence, list):
        raise ValueError("evidence must be a list")
    found = set()
    for e in evidence:
        if not isinstance(e, dict) or set(e) != {"label_id", "quote", "explanation"}:
            raise ValueError("Invalid evidence schema")
        if e["label_id"] not in labels:
            raise ValueError("Evidence label absent from labels")
        if not isinstance(e["quote"], str) or not e["quote"].strip() or e["quote"] not in text:
            raise ValueError("Evidence quote is not an exact nonempty substring of target text")
        if not isinstance(e["explanation"], str) or not e["explanation"].strip():
            raise ValueError("Missing evidence explanation")
        found.add(e["label_id"])
    if found != set(labels):
        raise ValueError("Each predicted label needs evidence")
    return obj
