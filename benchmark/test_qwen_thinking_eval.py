import json
import unittest

from run_atlas_vlm import parse_geometry
from run_qwen_thinking_eval import IncompleteThinking, final_answer, generation_settings
from report_qwen_thinking_eval import paired, summary


class ThinkingAnswerTests(unittest.TestCase):
    def setUp(self):
        self.row = {"event_id": "Z0001", "width": 1538, "height": 1754}
        self.answer = json.dumps({"event_id": "Z0001", "geometry": {"type": "point", "coordinates": [[3, 4]]}})

    def test_instruct_unchanged(self):
        self.assertEqual(final_answer(self.answer, False), self.answer)

    def test_thinking_prefix_may_be_in_template(self):
        self.assertEqual(final_answer("reasoning\n</think>\n" + self.answer, True), self.answer)

    def test_explicit_think_block(self):
        self.assertEqual(final_answer("<think>reasoning</think>" + self.answer, True), self.answer)

    def test_unfinished_reasoning_is_not_an_answer(self):
        with self.assertRaises(IncompleteThinking):
            final_answer("Perhaps answer: " + self.answer, True)

    def test_ignore_draft_answer_in_reasoning(self):
        raw = self.answer + "</think>" + json.dumps({"event_id": "Z0001", "geometry": None})
        self.assertIsNone(parse_geometry(final_answer(raw, True), self.row)["geometry"])

    def test_instruct_reasoning_is_not_silently_removed(self):
        with self.assertRaises(ValueError):
            final_answer("<think>draft</think>" + self.answer, False)

    def test_nested_or_multiple_thinking_rejected(self):
        for raw in ("a</think>b</think>" + self.answer, "a</think><think>" + self.answer):
            with self.assertRaises(ValueError):
                final_answer(raw, True)

    def test_no_geometry_repairs(self):
        raw = '{"event_id":"Z0001","geometry":{"type":"point","coordinates":[3,4]}}'
        with self.assertRaises(ValueError):
            parse_geometry(final_answer("draft</think>" + raw, True), self.row)

    def test_padding_output_still_invalid(self):
        raw = '{"event_id":"Z0001","geometry":{"type":"point","coordinates":[[1550,5]]}}'
        with self.assertRaises(ValueError):
            parse_geometry(final_answer(raw, False), self.row)

    def test_paired_statistics_exclude_missing_and_mismatched_geometry(self):
        rows = {
            "a": {"Z1": {"gold_type": "point", "distance_to_gold_px": 30},
                  "Z2": {"gold_type": "point", "status": "error"}},
            "b": {"Z1": {"gold_type": "point", "distance_to_gold_px": 10},
                  "Z2": {"gold_type": "point", "distance_to_gold_px": 0}},
        }
        result = paired(rows, ("a", "b"))
        self.assertEqual(result["event_ids"], ["Z1"])
        self.assertEqual(result["methods"]["a"]["mean_px"], 30)
        self.assertEqual(result["methods"]["b"]["mean_px"], 10)

    def test_output_coverage_is_separate_from_spatial_accuracy(self):
        rows = {
            "Z1": {"gold_type": "point", "status": "valid", "distance_to_gold_px": 200},
            "Z2": {"gold_type": "point", "status": "error", "error_type": "IncompleteThinking"},
            "Z0003": {"gold_type": None, "status": "abstained", "outside_map_abstention": True},
        }
        result = summary(rows, [{"event_id": "Z2", "elapsed_seconds": 10,
                                 "usage": {"output_tokens": 4096, "reached_token_limit": True}}])
        self.assertEqual(result["point_n"], 1)
        self.assertEqual(result["point_mean_px"], 200)
        self.assertEqual(result["errors"], 1)
        self.assertEqual(result["error_types"], {"IncompleteThinking": 1})
        self.assertEqual(result["abstained"], 1)
        self.assertEqual(result["token_limit_ids"], ["Z2"])

    def test_provider_reasoning_tokens_are_not_reported_as_zero(self):
        attempts = [{"event_id": "Z1", "elapsed_seconds": 1,
                     "usage": {"output_tokens_details": {"reasoning_tokens": 12}}}]
        self.assertEqual(summary({}, attempts)["thinking_tokens"], 12)

    def test_unreported_reasoning_tokens_remain_unknown(self):
        attempts = [{"event_id": "Z1", "elapsed_seconds": 1, "usage": {}}]
        self.assertIsNone(summary({}, attempts)["thinking_tokens"])


class GenerationPresetTests(unittest.TestCase):
    def test_default_preserves_greedy_budget(self):
        for mode in ("instruct", "thinking"):
            self.assertEqual(generation_settings(mode), {"max_new_tokens": 4096, "do_sample": False})

    def test_hf_model_card_vl_parameters(self):
        self.assertEqual(generation_settings("thinking", "hf-thinking-vl"), {
            "max_new_tokens": 40960, "do_sample": True, "temperature": 1.0,
            "top_p": 0.95, "top_k": 20, "repetition_penalty": 1.0,
        })

    def test_explicit_budget_override(self):
        self.assertEqual(generation_settings("thinking", "hf-thinking-vl", 8192)["max_new_tokens"], 8192)

    def test_thinking_preset_rejects_instruct(self):
        with self.assertRaises(ValueError):
            generation_settings("instruct", "hf-thinking-vl")

    def test_invalid_budget_and_preset(self):
        for budget in (0, -1):
            with self.assertRaises(ValueError):
                generation_settings("thinking", max_tokens=budget)
        with self.assertRaises(ValueError):
            generation_settings("thinking", "unknown")


if __name__ == "__main__":
    unittest.main()
