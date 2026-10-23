import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import eval_geometry as ev

W, H = 1000, 800
SQUARE = {"type": "polygon", "coordinates": [[100, 100], [300, 100], [300, 300], [100, 300]]}
BIG = {"type": "polygon", "coordinates": [[0, 0], [900, 0], [900, 700], [0, 700]]}
LINE = {"type": "line", "coordinates": [[100, 500], [500, 500], [800, 400]]}


class ScoreEvent(unittest.TestCase):
    def test_identical_polygon(self):
        r = ev.score_event(SQUARE, SQUARE, W, H)
        self.assertAlmostEqual(r["iou"], 1.0)
        self.assertTrue(r["hit@0.75"])

    def test_disjoint_polygon(self):
        far = {"type": "polygon", "coordinates": [[600, 600], [700, 600], [700, 700]]}
        r = ev.score_event(SQUARE, far, W, H)
        self.assertEqual(r["iou"], 0.0)
        self.assertFalse(r["point_in_region"])

    def test_point_inside_large_polygon_is_not_full_hit(self):
        pt = {"type": "point", "coordinates": [[450, 350]]}
        r = ev.score_event(BIG, pt, W, H)
        self.assertTrue(r["point_in_region"])
        self.assertLess(r["iou"], 0.1)
        self.assertFalse(r["hit@0.5"])
        self.assertFalse(r["type_match"])

    def test_point_vs_point(self):
        g = {"type": "point", "coordinates": [[400, 400]]}
        self.assertAlmostEqual(ev.score_event(g, g, W, H)["iou"], 1.0)
        near = {"type": "point", "coordinates": [[410, 400]]}
        self.assertTrue(ev.score_event(g, near, W, H)["hit@0.5"])

    def test_line_vs_same_line_and_shifted(self):
        self.assertAlmostEqual(ev.score_event(LINE, LINE, W, H)["iou"], 1.0)
        shifted = {"type": "line", "coordinates": [[x, y + 200] for x, y in LINE["coordinates"]]}
        self.assertEqual(ev.score_event(LINE, shifted, W, H)["iou"], 0.0)

    def test_abstention_cases(self):
        self.assertEqual(ev.score_event(None, None, W, H)["outcome"], "correct_abstention")
        self.assertEqual(ev.score_event(None, SQUARE, W, H)["outcome"], "false_presence")
        r = ev.score_event(SQUARE, None, W, H)
        self.assertEqual(r["outcome"], "false_abstention")
        self.assertEqual(r["iou"], 0.0)

    def test_invalid_prediction_is_not_repaired(self):
        bad = {"type": "point", "coordinates": [311, 100]}
        r = ev.score_event(SQUARE, bad, W, H)
        self.assertEqual(r["outcome"], "invalid_prediction")
        r = ev.score_event(SQUARE, SQUARE, W, H, pred_error="JSONDecodeError")
        self.assertEqual(r["outcome"], "invalid_prediction")
        self.assertEqual(r["iou"], 0.0)

    def test_stringified_geometry_accepted(self):
        r = ev.score_event(str(SQUARE), SQUARE, W, H)
        self.assertAlmostEqual(r["iou"], 1.0)


class Evaluate(unittest.TestCase):
    def test_missing_prediction_counts_as_zero(self):
        gold = {"A": {"geometry": SQUARE, "width": W, "height": H},
                "B": {"geometry": LINE, "width": W, "height": H}}
        res = ev.evaluate(gold, {"A": {"event_id": "A", "geometry": SQUARE}})
        self.assertEqual(res["summary"]["all"]["n"], 2)
        self.assertAlmostEqual(res["summary"]["all"]["mean_iou"], 0.5)
        self.assertEqual(res["summary"]["line"]["outcomes"], {"invalid_prediction": 1})

    def test_load_review_gold_prefers_human_geometry(self):
        with tempfile.TemporaryDirectory() as d:
            ann = Path(d, "a.jsonl")
            rev = Path(d, "r.jsonl")
            img = {"path": "x.jpg", "width": W, "height": H}
            ann.write_text("\n".join(json.dumps(r) for r in [
                {"event_id": "A", "status": "proposed", "geometry": BIG, "annotation_image": img},
                {"event_id": "B", "status": "proposed", "geometry": SQUARE, "annotation_image": img},
            ]))
            rev.write_text("\n".join(json.dumps(r) for r in [
                {"event_id": "A", "decision": "accepted"},
                {"event_id": "A", "decision": "modified_accepted", "human_geometry": str(SQUARE)},
                {"event_id": "B", "decision": "rejected"},
            ]))
            gold = ev.load_review_gold(ann, rev)
        self.assertEqual(list(gold), ["A"])
        self.assertEqual(gold["A"]["geometry"]["coordinates"], SQUARE["coordinates"])

    def test_stale_review_is_not_gold(self):
        with tempfile.TemporaryDirectory() as d:
            ann = Path(d, "a.jsonl")
            rev = Path(d, "r.jsonl")
            img = {"path": "x.jpg", "width": W, "height": H}
            cands = [{"event_id": "A", "status": "proposed", "geometry": SQUARE, "annotation_image": img},
                     {"event_id": "B", "status": "proposed", "geometry": SQUARE, "annotation_image": img}]
            ann.write_text("\n".join(json.dumps(r) for r in cands))
            rev.write_text("\n".join(json.dumps(r) for r in [
                {"event_id": "A", "decision": "accepted", "candidate_sha256": ev.candidate_digest(cands[0])},
                {"event_id": "B", "decision": "accepted", "candidate_sha256": "0" * 64},
            ]))
            gold = ev.load_review_gold(ann, rev)
        self.assertEqual(list(gold), ["A"])

    def test_no_location_review_is_abstention_gold(self):
        with tempfile.TemporaryDirectory() as d:
            ann = Path(d, "a.jsonl")
            rev = Path(d, "r.jsonl")
            img = {"path": "x.jpg", "width": W, "height": H}
            ann.write_text(json.dumps({"event_id": "C", "status": "proposed", "geometry": SQUARE, "annotation_image": img}))
            rev.write_text(json.dumps({"event_id": "C", "decision": "accepted_no_location", "human_geometry": None}))
            gold = ev.load_review_gold(ann, rev)
        self.assertIsNone(gold["C"]["geometry"])
        self.assertEqual(ev.score_event(None, None, W, H)["outcome"], "correct_abstention")
        self.assertEqual(ev.score_event(None, SQUARE, W, H)["outcome"], "false_presence")


if __name__ == "__main__":
    unittest.main()
