import copy
import csv
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from narrative_bench.annotations import export_sheet, import_sheet, read_sheet
from narrative_bench.baseline import TfidfCentroid
from narrative_bench.cli import baseline, compare
from narrative_bench.data import read_json, read_jsonl, validate_dataset, validate_prediction
from narrative_bench.engine import calculated_cost, execute, validate_config
from narrative_bench.evaluate import evaluate
from narrative_bench.metrics import agreement, classification, cluster_bootstrap
from narrative_bench.prompts import messages

ROOT = Path(__file__).resolve().parents[1]


class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.rows = read_jsonl(ROOT / "data/demo/records.jsonl")
        self.tax = read_json(ROOT / "data/demo/taxonomy.json")
        self.cfg = read_json(ROOT / "configs/demo.json")
        temp_root = ROOT / "tests" / ".tmp"
        temp_root.mkdir(exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=temp_root)
        self.out = Path(self.tmp.name) / "run"

    def tearDown(self):
        resolved = Path(self.tmp.name).resolve()
        if not resolved.is_relative_to((ROOT / "tests" / ".tmp").resolve()):
            raise RuntimeError("Unexpected test cleanup path")
        self.tmp.cleanup()

    def test_article_leakage_rejected(self):
        self.rows[-1]["article_id"] = self.rows[0]["article_id"]
        with self.assertRaisesRegex(ValueError, "leakage"):
            validate_dataset(self.rows, self.tax)

    def test_normalized_text_leakage_rejected(self):
        self.rows[-1]["text"] = "  " + self.rows[0]["text"].upper() + "  "
        with self.assertRaisesRegex(ValueError, "leakage"):
            validate_dataset(self.rows, self.tax)

    def test_mixed_demo_research_rejected(self):
        self.rows[0]["dataset_kind"] = "research"
        with self.assertRaises(ValueError):
            validate_dataset(self.rows, self.tax)

    def test_duplicate_id_rejected(self):
        self.rows[-1]["id"] = self.rows[0]["id"]
        with self.assertRaises(ValueError):
            validate_dataset(self.rows, self.tax)

    def test_unknown_gold_label_rejected(self):
        self.rows[0]["labels"] = ["invented"]
        with self.assertRaises(ValueError):
            validate_dataset(self.rows, self.tax)

    def test_exact_quote_required(self):
        obj = {"labels": ["a"], "evidence": [{"label_id": "a", "quote": "invented", "explanation": "test"}]}
        with self.assertRaisesRegex(ValueError, "substring"):
            validate_prediction(obj, "source", ["a"])

    def test_evidence_coverage_required(self):
        with self.assertRaises(ValueError):
            validate_prediction({"labels": ["a"], "evidence": []}, "source", ["a"])

    def test_negative_prediction_schema(self):
        self.assertEqual(validate_prediction({"labels": [], "evidence": []}, "source", ["a"])["labels"], [])

    def test_gold_never_enters_zero_shot(self):
        r = copy.deepcopy(self.rows[0])
        original = messages(r, self.tax)
        r["labels"] = ["MAGIC_SECRET_GOLD"]
        self.assertEqual(messages(r, self.tax), original)

    def test_dev_examples_rejected(self):
        example = copy.deepcopy(self.rows[0])
        example["split"] = "dev"
        with self.assertRaises(ValueError):
            messages(self.rows[-1], self.tax, "few", [example])

    def test_metric_hand_calculation(self):
        m = classification([["a"], ["a", "b"], []], [["a"], ["b"], ["b"]], ["a", "b"])
        self.assertAlmostEqual(m["micro_f1"], 2 / 3)
        self.assertAlmostEqual(m["macro_f1_all_labels"], 2 / 3)
        self.assertAlmostEqual(m["exact_match"], 1 / 3)
        self.assertEqual(m["by_label"]["b"]["fp"], 1)

    def test_absent_label_and_empty_conventions(self):
        m = classification([[]], [[]], ["a"])
        self.assertEqual(m["macro_f1_all_labels"], 0)
        self.assertEqual(m["sample_f1_empty_empty_zero"], 0)
        self.assertEqual(m["exact_match"], 1)

    def test_cached_cost_unknown_without_rate(self):
        usage = {"prompt_tokens": 1000, "completion_tokens": 100, "prompt_tokens_details": {"cached_tokens": 200}}
        self.assertIsNone(calculated_cost(usage, {"input": 1, "output": 2}))
        self.assertAlmostEqual(calculated_cost(usage, {"input": 1, "output": 2, "cached_input": .5}), .0011)

    def test_missing_usage_not_free(self):
        self.assertIsNone(calculated_cost({}, {"input": 1, "output": 2}))
        self.assertIsNone(calculated_cost({"prompt_tokens": -1, "completion_tokens": 2}, {"input": 1, "output": 2}))

    def test_demo_end_to_end_and_resume(self):
        first = execute(self.rows, self.tax, self.cfg, self.out)
        before = (self.out / "predictions.jsonl").read_bytes()
        second = execute(self.rows, self.tax, self.cfg, self.out)
        self.assertEqual(before, (self.out / "predictions.jsonl").read_bytes())
        self.assertEqual(first["api_attempts"], second["api_attempts"])
        m = evaluate(self.rows, self.tax, self.out, bootstrap=20)
        self.assertEqual(m["dataset_kind"], "synthetic_demo")
        self.assertIn("DEMONSTRATION", m["warning"])
        self.assertTrue((self.out / "report.html").is_file())

    def test_changed_fingerprint_cannot_resume(self):
        execute(self.rows, self.tax, self.cfg, self.out)
        self.cfg["model"] = "changed"
        with self.assertRaisesRegex(ValueError, "fingerprint"):
            execute(self.rows, self.tax, self.cfg, self.out)

    def test_evaluation_hash_mismatch_rejected(self):
        execute(self.rows, self.tax, self.cfg, self.out)
        self.rows[0]["text"] += " Changed."
        with self.assertRaises(ValueError):
            evaluate(self.rows, self.tax, self.out, 0)

    def test_incomplete_run_retains_missing(self):
        self.cfg["max_api_calls"] = 2
        execute(self.rows, self.tax, self.cfg, self.out)
        m = evaluate(self.rows, self.tax, self.out, 0)
        self.assertEqual(m["coverage"]["selected"], 8)
        self.assertEqual(m["coverage"]["missing"], 6)

    def test_invalid_negative_not_success(self):
        execute(self.rows, self.tax, self.cfg, self.out)
        from narrative_bench.data import write_jsonl
        ps = read_jsonl(self.out / "predictions.jsonl")
        for p in ps:
            p["valid"] = False
        write_jsonl(self.out / "predictions.jsonl", ps)
        m = evaluate(self.rows, self.tax, self.out, 0)
        self.assertEqual(m["coverage"]["end_to_end_exact_match"], 0)
        self.assertEqual(m["coverage"]["valid"], 0)

    def test_bootstrap_uses_articles_and_reproducible(self):
        selected = [r for r in self.rows if r["split"] == "test"]
        a = cluster_bootstrap(selected, [r["labels"] for r in selected], [l["id"] for l in self.tax["labels"]], 30)
        b = cluster_bootstrap(selected, [r["labels"] for r in selected], [l["id"] for l in self.tax["labels"]], 30)
        self.assertEqual(a, b)
        self.assertEqual(a["unit"], "article")

    def test_baseline_only_fits_train(self):
        with self.assertRaises(ValueError):
            TfidfCentroid().fit([self.rows[-1]], ["a"])

    def test_baseline_complete_pipeline(self):
        baseline(self.rows, self.tax, self.out, "test")
        m = evaluate(self.rows, self.tax, self.out, 0)
        self.assertEqual(m["coverage"]["valid"], 8)
        self.assertEqual(m["resources"]["cost_usd_estimate"], 0)

    def test_annotation_sheet_is_blinded(self):
        sheet = Path(self.tmp.name) / "annotation.csv"
        export_sheet(self.rows, sheet, "test")
        with sheet.open(encoding="utf-8-sig", newline="") as stream:
            self.assertTrue(all(r["labels_json"] == "" for r in csv.DictReader(stream)))
        with self.assertRaises(ValueError):
            read_sheet(sheet, ["a"])

    def test_annotation_import_rejects_changed_text(self):
        sheet = Path(self.tmp.name) / "annotation.csv"
        export_sheet(self.rows, sheet, "new")
        with sheet.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            fields, entries = reader.fieldnames, list(reader)
        for item in entries:
            item["labels_json"] = "[]"
        entries[0]["text"] += " changed"
        with sheet.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(entries)
        with self.assertRaisesRegex(ValueError, "source text"):
            import_sheet(sheet, self.rows, self.tax, "new", Path(self.tmp.name) / "changed.jsonl")

    def test_agreement_degenerate_kappa(self):
        m = agreement({"x": [], "y": []}, {"x": [], "y": []}, ["a"])
        self.assertIsNone(m["per_label_binary_cohen_kappa"]["a"])
        self.assertEqual(m["set_exact_agreement"], 1)

    def test_agreement_requires_matching_ids(self):
        with self.assertRaises(ValueError):
            agreement({"x": []}, {"y": []}, ["a"])

    def test_api_requires_opt_in(self):
        cfg = read_json(ROOT / "configs/api.example.json")
        cfg["model"] = "test-model"
        with self.assertRaisesRegex(ValueError, "execute-api"):
            execute(self.rows, self.tax, cfg, self.out)

    def test_secret_config_rejected(self):
        self.cfg["api_key"] = "not-a-real-secret"
        with self.assertRaises(ValueError):
            validate_config(self.cfg)

    def test_http_adapter_real_local_transport(self):
        received = []
        class Handler(BaseHTTPRequestHandler):
            def do_POST(server):
                payload = json.loads(server.rfile.read(int(server.headers["Content-Length"])))
                received.append(payload)
                result = {"id": "local-test-response", "model": "local-test-model", "choices": [{"message": {"content": '{"labels":[],"evidence":[]}'}, "finish_reason": "stop"}],
                          "usage": {"prompt_tokens": 100, "completion_tokens": 10}}
                encoded = json.dumps(result).encode()
                server.send_response(200)
                server.send_header("Content-Type", "application/json")
                server.send_header("Content-Length", str(len(encoded)))
                server.end_headers()
                server.wfile.write(encoded)
            def log_message(*args):
                pass
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        cfg = read_json(ROOT / "configs/api.example.json")
        cfg.update(model="test-model", endpoint=f"http://127.0.0.1:{server.server_port}/chat/completions", allow_local_http=True, delay_seconds=0,
                   pricing_usd_per_million={"input": 1, "output": 2})
        try:
            with patch.dict(os.environ, {"NARRATIVE_API_KEY": "local-test-token"}):
                execute(self.rows, self.tax, cfg, self.out, limit=1, live=True)
            m = evaluate(self.rows, self.tax, self.out, 0)
            self.assertAlmostEqual(m["resources"]["cost_usd_estimate"], .00012)
            self.assertEqual(len(received), 1)
            self.assertNotIn("local-test-token", (self.out / "manifest.json").read_text())
        finally:
            server.shutdown()
            server.server_close()
            worker.join()

    def test_invalid_json_is_counted_and_costed_without_retry(self):
        cfg = read_json(ROOT / "configs/api.example.json")
        cfg.update(model="test-model", delay_seconds=0, pricing_usd_per_million={"input": 1, "output": 2})
        response = {"choices": [{"message": {"content": "not JSON"}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 100, "completion_tokens": 10}}
        with patch.dict(os.environ, {"NARRATIVE_API_KEY": "local-test-token"}), patch("narrative_bench.engine.http_complete", return_value=response) as call:
            execute(self.rows, self.tax, cfg, self.out, limit=1, live=True)
        self.assertEqual(call.call_count, 1)
        m = evaluate(self.rows, self.tax, self.out, 0)
        self.assertEqual(m["coverage"]["valid"], 0)
        self.assertAlmostEqual(m["resources"]["cost_usd_estimate"], .00012)

    def test_retry_records_unknown_error_cost(self):
        cfg = read_json(ROOT / "configs/api.example.json")
        cfg.update(model="test-model", delay_seconds=0, pricing_usd_per_million={"input": 1, "output": 2})
        response = {"choices": [{"message": {"content": '{"labels":[],"evidence":[]}'}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 100, "completion_tokens": 10}}
        err = HTTPError(cfg["endpoint"], 429, "retry", {}, None)
        with patch.dict(os.environ, {"NARRATIVE_API_KEY": "local-test-token"}), patch("narrative_bench.engine.http_complete", side_effect=[err, response]), patch("narrative_bench.engine.time.sleep"):
            execute(self.rows, self.tax, cfg, self.out, limit=1, live=True)
        m = evaluate(self.rows, self.tax, self.out, 0)
        self.assertIsNone(m["resources"]["cost_usd_estimate"])
        self.assertEqual(m["resources"]["attempts"], 2)
        self.assertAlmostEqual(m["resources"]["known_cost_usd_lower_bound"], .00012)

    def test_compare_rejects_different_selected_samples(self):
        execute(self.rows, self.tax, self.cfg, self.out, limit=2)
        evaluate(self.rows, self.tax, self.out, 0)
        second = Path(self.tmp.name) / "second"
        execute(self.rows, self.tax, self.cfg, second, limit=3)
        evaluate(self.rows, self.tax, second, 0)
        with self.assertRaises(ValueError):
            compare([self.out, second], Path(self.tmp.name) / "summary.csv")


if __name__ == "__main__":
    unittest.main()
