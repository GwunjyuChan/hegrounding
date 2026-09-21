import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import run_qwen_grounding_comparison as workflow
from run_atlas_vlm import task_prompt


class GroundingComparisonTests(unittest.TestCase):
    def setUp(self):
        self.row = {"event_id": "Z1", "map_version": "v1", "image": "map.png",
                    "width": 100, "height": 80, "text": "The unit camped near Town. SECRET DISTRACTOR",
                    "question": "Where was the camp?"}
        self.answer = {"event_id": "Z1", "answer_location": "near Town", "evidence_quotes": ["camped near Town"], "uncertainty": "Exact site unknown."}

    def test_stage1_has_no_image_metadata(self):
        self.assertEqual(set(workflow.text_task(self.row)), {"event_id", "passage", "question"})

    def test_stage2_contains_only_generated_text_and_same_question(self):
        derived = workflow.grounding_task(self.row, {**self.answer, "human_annotation": "SECRET GOLD"})
        request = json.loads(task_prompt(derived))
        self.assertEqual(request["question"], self.row["question"])
        self.assertEqual(request["width"], 100)
        self.assertNotIn("SECRET", task_prompt(derived))
        self.assertEqual(json.loads(request["passage"])["uncertainty"], self.answer["uncertainty"])

    def test_stage2_rejects_wrong_identity_and_abstention(self):
        for change in ({"event_id": "Z2"}, {"answer_location": None}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                workflow.grounding_task(self.row, {**self.answer, **change})

    def run_mocked(self, answer_raw, map_raw=None):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        output = Path(temp.name)
        geom = map_raw or '{"event_id":"Z1","geometry":{"type":"point","coordinates":[[10,20]]}}'
        with patch.object(workflow, "call_local", return_value=(answer_raw, {"input_tokens": 5}, {})), \
             patch.object(workflow, "call_local_qwen", return_value=(geom, {"image_grid_thw": [[1, 2, 2]]})) as maps:
            results = workflow.run_comparison((None, None, {}), b"same-image", [self.row], "same-prompt",
                {"map_version": "v1", "image_sha256": "hash"}, output, "Qwen/test", 32, 64)
        return results, output, maps

    def test_matched_image_prompt_and_map_budget(self):
        results, output, calls = self.run_mocked(json.dumps(self.answer))
        self.assertEqual(calls.call_count, 2)
        a, b = [c.args for c in calls.call_args_list]
        self.assertEqual(a[1], b[1])
        self.assertEqual(a[3:], b[3:])
        self.assertNotEqual(a[2]["text"], b[2]["text"])
        self.assertEqual(results["two_stage"]["errors"], [])
        self.assertEqual(json.loads((output / "stage1/answers.json").read_text())["answers"][0]["quote_not_verbatim"], [])

    def test_upstream_error_does_not_fallback_or_count_as_abstention(self):
        results, output, calls = self.run_mocked("invalid JSON")
        self.assertEqual(calls.call_count, 1)
        self.assertEqual(results["two_stage"]["predictions"], [])
        self.assertEqual(results["two_stage"]["errors"][0]["error_type"], "Stage1Error")
        self.assertEqual(json.loads((output / "two_stage/attempts.jsonl").read_text())["status"], "upstream_error")

    def test_upstream_abstention_is_separate_from_parse_error(self):
        results, output, calls = self.run_mocked(json.dumps({**self.answer, "answer_location": None, "evidence_quotes": []}))
        self.assertEqual(calls.call_count, 1)
        self.assertEqual(results["two_stage"]["errors"], [])
        self.assertIsNone(results["two_stage"]["predictions"][0]["geometry"])
        self.assertEqual(json.loads((output / "two_stage/attempts.jsonl").read_text())["status"], "upstream_abstained")

    def test_invalid_map_coordinates_preserved_as_errors(self):
        results, output, _ = self.run_mocked(json.dumps(self.answer), '{"event_id":"Z1","geometry":{"type":"point","coordinates":[[100,80]]}}')
        self.assertTrue(all(len(r["errors"]) == 1 for r in results.values()))
        self.assertIn("[100,80]", json.loads((output / "direct/attempts.jsonl").read_text())["raw"])


if __name__ == "__main__":
    unittest.main()
