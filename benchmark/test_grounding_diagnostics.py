import unittest

from compare_grounding_methods import costs, diagnose, paired_points, point_distance


class GroundingDiagnosticsTests(unittest.TestCase):
    def setUp(self):
        self.gold = {"status": "accepted", "geometry": {"type": "point", "coordinates": [[0, 0]]}}
        self.pred = {"geometry": {"type": "point", "coordinates": [[3, 4]]}}

    def test_point_distance(self):
        self.assertEqual(point_distance([3, 4], self.gold["geometry"]), 5)

    def test_open_line_and_polygon_boundaries(self):
        line = {"type": "line", "coordinates": [[0, 0], [10, 0], [10, 10]]}
        self.assertEqual(point_distance([5, 5], line), 5)
        polygon = {"type": "polygon", "coordinates": [[0, 0], [10, 0], [10, 10], [0, 10]]}
        self.assertEqual(point_distance([0, 5], polygon), 0)
        self.assertEqual(point_distance([5, 5], polygon), 0)
        self.assertEqual(point_distance([13, 5], polygon), 3)

    def test_excluded_and_errors_never_get_distance(self):
        self.assertNotIn("distance_to_gold_px", diagnose(self.gold, self.pred, excluded=True))
        self.assertNotIn("distance_to_gold_px", diagnose(self.gold, None, error={"error_type": "Failed"}))
        self.assertEqual(diagnose(self.gold, {"geometry": None})["status"], "abstained")

    def test_outside_map_and_upstream_failure(self):
        gold = {"status": "outside_map", "geometry": None}
        self.assertTrue(diagnose(gold, {"geometry": None})["outside_map_abstention"])
        self.assertFalse(diagnose(gold, self.pred)["outside_map_abstention"])
        self.assertNotIn("outside_map_abstention", diagnose(gold, None, error={"error_type": "Stage1Error"}))

    def test_matched_pairs_exclude_failures_and_polygon_metrics(self):
        good = {"gold_type": "point", "distance_to_gold_px": 5}
        rows = [{"event_id": "A", "direct": good, "two_stage": {**good, "distance_to_gold_px": 3}},
                {"event_id": "B", "direct": good, "two_stage": {"status": "error"}},
                {"event_id": "C", "direct": {**good, "gold_type": "polygon"}, "two_stage": good}]
        pair = paired_points(rows)
        self.assertEqual(pair["event_ids"], ["A"])
        self.assertEqual(pair["improved"], 1)
        self.assertEqual(pair["two_stage"]["mean_px"], 3)

    def test_costs_include_text_but_not_skipped_calls(self):
        result = costs([{"elapsed_seconds": 2, "usage": {"total_tokens": 10}},
                        {"elapsed_seconds": 3, "usage": {"total_tokens": 20}},
                        {"elapsed_seconds": 0, "map_call_skipped": True, "usage": None}])
        self.assertEqual(result["calls"], 2)
        self.assertEqual(result["seconds"], 5)
        self.assertEqual(result["total_tokens"], 30)


if __name__ == "__main__":
    unittest.main()
