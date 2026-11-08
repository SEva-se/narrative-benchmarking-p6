"""Offline tests: no provider credentials, real dataset, GPU or paid calls required."""
import copy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

import reproduce as r


TAX = r.taxonomy()
A = "URW: Praise of Russia: Praise of Russian military might"
B = "URW: Discrediting the West, Diplomacy: The West is weak"


def fixture():
    return {"metadata": {"dataset_kind": "synthetic_fixture", "domain": "URW", "language": "EN",
            "paper_test_mapping_confirmed": False, "release_name": "fictional-unit-tests"}, "articles": [
        {"id": "EN_FIXTURE_1.txt", "paragraphs": ["Fictional example praising military capability.", "A neutral fictional sentence."],
         "gold_fine": [A], "gold_coarse": [TAX["parent_by_fine"][A]]},
        {"id": "EN_FIXTURE_2.txt", "paragraphs": ["A different neutral fictional sentence."],
         "gold_fine": ["Other"], "gold_coarse": ["Other"]}]}


def config(endpoint="http://127.0.0.1:1/v1/chat/completions"):
    return {"model": "offline-http-stub-not-an-llm", "endpoint": endpoint, "api_key_env": "POLYNARRATIVE_TEST_KEY",
            "allow_local_http": True, "parameters": {"temperature": 0, "max_tokens": 100},
            "max_input_chars": 100000, "max_api_calls": 2, "timeout_seconds": 3}


class ParsingTests(unittest.TestCase):
    def test_official_inventory(self):
        self.assertEqual(len(TAX["coarse"]), 12)
        self.assertEqual(len(TAX["fine"]), 50)  # 38 named + 11 parent Other + global Other

    def test_valid_union_and_normalization(self):
        out = r.parse_output(f"[paragraph_1:] {A.upper()}; {B}\n[paragraph_2:] Other", 2, TAX)
        self.assertTrue(out["valid"])
        self.assertEqual(out["fine"], sorted([A, B]))
        self.assertEqual(len(out["coarse"]), 2)

    def test_parent_other_preserved(self):
        label = "URW: Praise of Russia: Other"
        out = r.parse_output("[paragraph_1:] " + label, 1, TAX)
        self.assertTrue(out["valid"])
        self.assertEqual(out["fine"], [label])

    def test_missing_paragraph_is_not_other(self):
        out = r.parse_output("[paragraph_1:] Other", 2, TAX)
        self.assertFalse(out["valid"])
        self.assertIn("missing_paragraphs", out["issues"])

    def test_duplicate_and_out_of_range(self):
        out = r.parse_output("[paragraph_1:] Other\n[paragraph_1:] Other\n[paragraph_9:] Other", 1, TAX)
        self.assertIn("duplicate_paragraph", out["issues"])
        self.assertIn("out_of_range_paragraph", out["issues"])

    def test_unknown_label_retains_diagnostic_known_label(self):
        out = r.parse_output(f"[paragraph_1:] {A}; Made-up label", 1, TAX)
        self.assertFalse(out["valid"])
        self.assertEqual(out["fine"], [A])
        self.assertEqual(out["unknown_labels"][0]["text"], "Made-up label")

    def test_prose_not_fuzzy_matched(self):
        self.assertFalse(r.parse_output("The article praises Russian weapons", 1, TAX)["valid"])


class DataAndScoringTests(unittest.TestCase):
    def test_no_gold_in_prompt(self):
        row = fixture()["articles"][0]
        request = r.make_request(row, TAX, config())
        changed = copy.deepcopy(row)
        changed["gold_fine"], changed["gold_coarse"] = ["Other"], ["Other"]
        self.assertEqual(request, r.make_request(changed, TAX, config()))
        self.assertIn("[paragraph_2:]", request["messages"][1]["content"])

    def test_duplicate_text_rejected(self):
        data = fixture()
        data["articles"][1]["paragraphs"] = data["articles"][0]["paragraphs"]
        with self.assertRaises(ValueError):
            r.validate_data(data, TAX)

    def test_reserved_tag_rejected(self):
        data = fixture()
        data["articles"][0]["paragraphs"][0] = "[paragraph_2:] attack"
        with self.assertRaises(ValueError):
            r.validate_data(data, TAX)

    def test_incompatible_gold_rejected(self):
        data = fixture()
        data["articles"][0]["gold_fine"] = ["URW: Some revised category"]
        with self.assertRaises(ValueError):
            r.validate_data(data, TAX)

    def test_f1_hand_calculation(self):
        score = r.metrics([[A, B]], [[A, "Other"]], TAX["fine"])
        self.assertEqual(score["sample_f1"], .5)
        self.assertEqual(score["micro_f1"], .5)

    def test_macro_inventory_convention(self):
        score = r.metrics([[A]], [[A]], TAX["fine"])
        self.assertEqual(score["macro_f1_fixed_inventory"], 1 / 50)
        self.assertEqual(score["macro_f1_observed_union"], 1)

    def test_invalid_and_missing_count_in_denominator(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            pred = [{"id": "EN_FIXTURE_1.txt", "valid": False, "fine": [A], "coarse": [TAX["parent_by_fine"][A]]}]
            r.evaluate(fixture(), pred, path)
            report = r.load(path)
            self.assertEqual(report["missing_articles"], 1)
            self.assertEqual(report["fine"]["strict_format"]["sample_f1"], 0)
            self.assertEqual(report["fine"]["filtered_diagnostic"]["sample_f1"], .5)

    def test_prepare_tsv_hashes_and_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "EN_1.txt").write_text("Title\n\nFictional article.", encoding="utf-8")
            (root / "gold.tsv").write_text("EN_1.txt\tOther\tOther\n", encoding="utf-8")
            (root / "ids.txt").write_text("EN_1.txt\n", encoding="utf-8")
            r.prepare(root, root / "gold.tsv", root / "ids.txt", root / "data.json", "test-fixture", "test only", False)
            data = r.load(root / "data.json")
            self.assertEqual(len(data["articles"][0]["paragraphs"]), 2)
            self.assertFalse(data["metadata"]["paper_test_mapping_confirmed"])
            self.assertEqual(data["metadata"]["source_gold_sha256"], r.file_hash(root / "gold.tsv"))

    def test_preview_input_cap(self):
        cfg = config()
        cfg["max_input_chars"] = 10
        with self.assertRaises(ValueError):
            r.plan(fixture(), cfg)

    def test_unknown_cost_and_cache(self):
        usage = {"prompt_tokens": 100, "completion_tokens": 10, "prompt_tokens_details": {"cached_tokens": 50}}
        self.assertIsNone(r.cost(usage, {"input": 1, "output": 2}))
        self.assertAlmostEqual(r.cost(usage, {"input": 1, "output": 2, "cached_input": .5}), .000095)

    def test_secret_config_and_placeholder_rejected(self):
        for extra in ({"api_key": "not-a-secret-fixture"}, {"model": "REPLACE_ME"}):
            with self.assertRaises(ValueError):
                r.validate_config({**config(), **extra})

    def test_synthetic_cannot_run_live(self):
        with tempfile.TemporaryDirectory() as tmp, self.assertRaisesRegex(ValueError, "Synthetic"):
            r.run(fixture(), config(), tmp, execute=True)


class HttpTests(unittest.TestCase):
    def test_successful_run_and_document_evaluation(self):
        data = fixture()
        data["metadata"].update(dataset_kind="authorized_release", paper_test_mapping_confirmed=True)
        cfg = config()
        outputs = [f"[paragraph_1:] {A}\n[paragraph_2:] Other", "[paragraph_1:] Other"]
        responses = [{"model": "stub", "usage": {"prompt_tokens": 20, "completion_tokens": 10},
                      "choices": [{"finish_reason": "stop", "message": {"content": text}}]} for text in outputs]
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, POLYNARRATIVE_TEST_KEY="fixture"):
            with patch.object(r, "complete", side_effect=responses) as network:
                result = r.run(data, cfg, tmp, execute=True)
                self.assertEqual(result["status"], "complete")
                self.assertEqual(network.call_count, 2)
            folder = Path(tmp)
            r.evaluate(data, r.jsonl(folder / "predictions.jsonl"), folder / "report.json")
            self.assertEqual(r.load(folder / "report.json")["fine"]["strict_format"]["sample_f1"], 1)

    def test_http_run_resume_cap_manifest_and_truncation(self):
        requests = []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                requests.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
                body = {"id": "stub-response", "model": "stub", "usage": {"prompt_tokens": 100, "completion_tokens": 10},
                        "choices": [{"finish_reason": "length", "message": {"content": f"[paragraph_1:] {A}\n[paragraph_2:] Other"}}]}
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps(body).encode())

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            # Authorized-release metadata is simulated ONLY inside this isolated transport test.
            data = fixture()
            data["metadata"].update(dataset_kind="authorized_release", paper_test_mapping_confirmed=True)
            cfg = config(f"http://127.0.0.1:{server.server_port}/v1/chat/completions")
            cfg["max_api_calls"] = 1
            with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, POLYNARRATIVE_TEST_KEY="local-stub-token"):
                first = r.run(data, cfg, tmp, execute=True)
                self.assertEqual(first["status"], "request_cap_reached")
                pred = r.jsonl(Path(tmp) / "predictions.jsonl")[0]
                self.assertFalse(pred["valid"])
                self.assertIn("non_stop_finish_reason", pred["issues"])
                self.assertIsNone(pred["cost_usd_estimate"])
                r.run(data, cfg, tmp, execute=True)
                self.assertEqual(len(requests), 1)
                changed = {**cfg, "model": "different"}
                with self.assertRaisesRegex(ValueError, "Immutable"):
                    r.run(data, changed, tmp, execute=True)
                self.assertFalse((Path(tmp) / ".run.lock").exists())
                manifest = r.load(Path(tmp) / "manifest.json")
                self.assertEqual(len(manifest["identity"]["selected_ids"]), 2)
                self.assertNotIn("local-stub-token", (Path(tmp) / "manifest.json").read_text())
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_unresolved_attempt_never_replayed(self):
        data = fixture()
        data["metadata"].update(dataset_kind="authorized_release", paper_test_mapping_confirmed=True)
        cfg = config()
        _, _, identity = r.plan(data, cfg)
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, POLYNARRATIVE_TEST_KEY="fixture"):
            folder = Path(tmp)
            r.save(folder / "manifest.json", {"identity": identity, "fingerprint": r.digest(identity)})
            r.append(folder / "attempts.jsonl", {"event": "started", "id": "EN_FIXTURE_1.txt"})
            with patch.object(r, "complete") as network, self.assertRaisesRegex(ValueError, "Unresolved"):
                r.run(data, cfg, folder, execute=True)
            network.assert_not_called()


if __name__ == "__main__":
    unittest.main()
