import unittest

from report import paired, score_text


class ComparisonTests(unittest.TestCase):
    def test_paired_subset_excludes_missing_and_region_scores(self):
        rows = {
            "a": {"one": {"gold_type": "point", "distance_to_gold_px": 10},
                  "two": {"gold_type": "point", "distance_to_gold_px": 100},
                  "three": {"gold_type": "polygon", "distance_to_gold_px": 0}},
            "b": {"one": {"gold_type": "point", "distance_to_gold_px": 20},
                  "two": {"gold_type": "point", "status": "error"},
                  "three": {"gold_type": "polygon", "distance_to_gold_px": 0}},
        }
        p = paired(rows, ("a", "b"), ("one", "two", "three"))
        self.assertEqual(p["event_ids"], ["one"])
        self.assertEqual(p["models"]["a"]["mean_px"], 10)
        self.assertEqual(p["models"]["b"]["mean_px"], 20)

    def test_empty_subset_has_no_zero_error(self):
        p = paired({"a": {}, "b": {}}, ("a", "b"), [])
        self.assertEqual(p["n"], 0)
        self.assertIsNone(p["models"]["a"]["mean_px"])

    def test_null_is_not_automatically_correct(self):
        self.assertEqual(score_text({"status": "abstained"}), "null")
        self.assertEqual(score_text({"status": "abstained", "outside_map_abstention": True}),
                         "correct outside-map null")


if __name__ == "__main__":
    unittest.main()
