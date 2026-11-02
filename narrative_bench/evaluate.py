"""Evaluate every selected record, retain failures and generate an inspectable report."""
import csv
import html
from pathlib import Path

from .data import digest, read_json, read_jsonl, validate_dataset, write_json
from .metrics import classification, cluster_bootstrap, percentile


def evaluate(rows, tax, run, bootstrap=500):
    info = validate_dataset(rows, tax)
    run = Path(run)
    manifest = read_json(run / "manifest.json")
    if any(manifest.get(k) != info[k] for k in ("dataset_sha256", "taxonomy_sha256")):
        raise ValueError("Evaluation data or taxonomy differs from the run manifest")
    by_id = {r["id"]: r for r in rows}
    ids = manifest["selected_ids"]
    if not ids or len(ids) != len(set(ids)) or any(i not in by_id for i in ids):
        raise ValueError("Invalid selected IDs in manifest")
    selected = [by_id[i] for i in ids]
    if any(r.get("labels") is None for r in selected):
        raise ValueError("Gold labels missing. Complete independent annotation before scoring")
    result_path = run / "predictions.jsonl"
    predictions = read_jsonl(result_path) if result_path.exists() else []
    if len({p["id"] for p in predictions}) != len(predictions) or set(p["id"] for p in predictions) - set(ids):
        raise ValueError("Duplicate or unexpected prediction IDs")
    index = {p["id"]: p for p in predictions}
    pred_labels, usable, exact_quotes, predicted_evidence, audits = [], [], 0, 0, []
    for r in selected:
        p = index.get(r["id"], {})
        valid = p.get("valid") is True
        obj = p.get("prediction") or {"labels": [], "evidence": []}
        # Revalidate persisted predictions rather than trusting a hand-edited valid flag.
        if valid:
            from .data import validate_prediction
            validate_prediction(obj, r["text"], [l["id"] for l in tax["labels"]])
        labels = obj["labels"] if valid else []
        pred_labels.append(labels)
        usable.append(valid)
        for e in obj["evidence"] if valid else []:
            predicted_evidence += 1
            exact_quotes += bool(e["quote"] and e["quote"] in r["text"])
            audits.append({"record_id": r["id"], "article_id": r["article_id"], "label_id": e["label_id"],
                          "text": r["text"], "quote": e["quote"], "explanation": e["explanation"],
                          "supports_label_0_1_unclear": "", "reviewer": "", "comment": ""})
    labels = [x["id"] for x in tax["labels"]]
    scores = classification([r["labels"] for r in selected], pred_labels, labels)
    latencies = [p["latency_seconds"] for p in predictions if isinstance(p.get("latency_seconds"), (float, int))]
    events_path = run / "attempts.jsonl"
    events = read_jsonl(events_path) if events_path.exists() else []
    starts = [e for e in events if e["event"] == "started"]
    responses = {e["event_id"]: e for e in events if e["event"] == "response"}
    is_api = manifest.get("config", {}).get("provider") == "chat_completions"
    unknown = sum(e["event_id"] not in responses or responses[e["event_id"]].get("cost_usd_estimate") is None for e in starts) if is_api else 0
    known_cost = sum(e.get("cost_usd_estimate") or 0 for e in responses.values())
    usage = {k: sum((e.get("usage") or {}).get(k, 0) or 0 for e in responses.values()) for k in ("prompt_tokens", "completion_tokens")}
    output = {"dataset_kind": info["dataset_kind"], "interpretation": manifest.get("interpretation"),
              "run_fingerprint": manifest["fingerprint"], "split": manifest["split"], "model": manifest.get("config", {}).get("model", "tfidf-centroid"),
              "variant": manifest.get("variant"), "classification": scores,
              "coverage": {"selected": len(ids), "valid": sum(usable), "invalid_or_missing": len(ids) - sum(usable),
                           "missing": sum(i not in index for i in ids), "valid_rate": sum(usable) / len(ids),
                           "end_to_end_exact_match": sum(ok and set(r["labels"]) == set(p) for r, p, ok in zip(selected, pred_labels, usable)) / len(ids)},
              "bootstrap": cluster_bootstrap(selected, pred_labels, labels, bootstrap),
              "evidence": {"quotes_in_valid_outputs": predicted_evidence, "exact_quotes": exact_quotes,
                           "semantic_support_score": None, "note": "Quote membership is checked. Semantic support requires blinded human review; invalid outputs remain failures."},
              "resources": {"attempts": len(starts), "observed_usage_subtotal": usage,
                            "cost_usd_estimate": None if unknown else known_cost, "known_cost_usd_lower_bound": known_cost,
                            "attempts_with_unknown_cost": unknown, "median_record_seconds": percentile(latencies, .5),
                            "p95_record_seconds": percentile(latencies, .95), "latency_definition": "Record wall time including retries/backoff, excluding inter-record delay",
                            "cost_definition": "Configured list-price estimate, not an invoice; usage subtotal may be incomplete"}}
    if info["dataset_kind"] == "synthetic_demo":
        output["warning"] = "SYNTHETIC DEMONSTRATION. These scores do not measure LLM capability or constitute research findings."
    write_json(run / "metrics.json", output)
    with (run / "evidence_review.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["record_id", "article_id", "label_id", "text", "quote", "explanation", "supports_label_0_1_unclear", "reviewer", "comment"])
        writer.writeheader()
        writer.writerows(audits)
    errors = []
    for r, p, valid in zip(selected, pred_labels, usable):
        if not valid or set(r["labels"]) != set(p):
            errors.append({"id": r["id"], "article_id": r["article_id"], "text": r["text"], "gold": ";".join(r["labels"]),
                           "predicted": ";".join(p), "valid": valid, "error_type": "", "analyst_note": ""})
    with (run / "errors.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["id", "article_id", "text", "gold", "predicted", "valid", "error_type", "analyst_note"])
        writer.writeheader()
        writer.writerows(errors)
    render_html(run / "report.html", output)
    return output


def render_html(path, m):
    esc = lambda x: html.escape(str(x))
    score = m["classification"]
    rows = "".join(f"<tr><td>{esc(k)}</td><td>{v['support']}</td><td>{v['precision']:.3f}</td><td>{v['recall']:.3f}</td><td>{v['f1']:.3f}</td></tr>" for k, v in score["by_label"].items())
    warning = m.get("warning", "Research run. Interpret with sample support, coverage and uncertainty.")
    cost = m["resources"]["cost_usd_estimate"]
    cost_text = "Unknown / incomplete" if cost is None else f"${cost:.6f}"
    text = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Narrative benchmark report</title><style>
body{{font:17px/1.65 system-ui,sans-serif;max-width:1040px;margin:48px auto;padding:0 28px;color:#15283b;background:#fafaf7}}
h1{{font-size:42px;line-height:1.15}}h2{{margin-top:40px}}aside{{padding:18px 22px;background:#fff0cd;border-left:5px solid #ba7200}}
table{{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}}td,th{{text-align:left;padding:11px;border-bottom:1px solid #cdd5db}}th{{color:#32556a}}code{{word-break:break-all;font-size:13px}}dt{{font-weight:700;margin-top:12px}}dd{{margin-left:0}}a{{color:#006c70}}
</style><h1>Narrative benchmark</h1><p>{esc(m['model'])} / {esc(m['variant'])} / {esc(m['split'])}</p>
<aside>{esc(warning)}</aside><h2>Classification</h2><dl>
<dt>Macro-F1, all taxonomy labels</dt><dd>{score['macro_f1_all_labels']:.3f}</dd>
<dt>Macro-F1, labels present in gold</dt><dd>{score['macro_f1_present_gold']:.3f}</dd>
<dt>Micro-F1</dt><dd>{score['micro_f1']:.3f}</dd>
<dt>Valid output coverage</dt><dd>{m['coverage']['valid']} / {m['coverage']['selected']}</dd>
<dt>End-to-end exact match</dt><dd>{m['coverage']['end_to_end_exact_match']:.3f}</dd></dl>
<p>Invalid and missing predictions count as empty label sets for F1. End-to-end exact match always counts them as failures. Absent-label F1 and empty/empty sample F1 use zero.</p>
<table><thead><tr><th>Label</th><th>Gold support</th><th>Precision</th><th>Recall</th><th>F1</th></tr></thead><tbody>{rows}</tbody></table>
<h2>Resources</h2><p>Estimated list-price cost: {cost_text}. Attempts with unknown cost: {m['resources']['attempts_with_unknown_cost']}.</p>
<p>Record median: {esc(m['resources']['median_record_seconds'])} seconds. p95: {esc(m['resources']['p95_record_seconds'])} seconds. These describe the deployment and include retry time.</p>
<h2>Evidence review</h2><p>Semantic support has not been scored automatically. Review evidence_review.csv independently. Exact quotation alone does not establish support for a label or internal model reasoning.</p>
<h2>Uncertainty and provenance</h2><p>{esc(m['bootstrap'])}</p><p>Run fingerprint: <code>{esc(m['run_fingerprint'])}</code></p>
<p><a href="metrics.json">Machine-readable metrics</a> / <a href="errors.csv">Error analysis</a> / <a href="evidence_review.csv">Human evidence review</a></p></html>'''
    Path(path).write_text(text, encoding="utf-8")
