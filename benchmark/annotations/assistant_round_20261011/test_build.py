import copy
import importlib.util
from pathlib import Path
import unittest


spec = importlib.util.spec_from_file_location("round_build", Path(__file__).with_name("build.py"))
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class AnnotationValidationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records, cls.assets = build.collect()

    def test_complete_active_scope(self):
        self.assertEqual(len(self.records), 139)
        self.assertEqual(len({r["event_id"] for r in self.records}), 139)
        self.assertEqual(len({r["annotation_image"]["path"] for r in self.records}), 26)

    def test_nothing_promoted_to_gold(self):
        for row in self.records:
            self.assertFalse(row["eligible_for_scoring"])
            self.assertEqual(row["human_review"], "pending")
            self.assertEqual(row["gold_status"], "not_gold")
            self.assertIsNone(row["tolerance_px"])

    def test_project_feature_vocabulary(self):
        for row in self.records:
            self.assertIn(row["feature_type"], build.FEATURE_TYPES)
            self.assertTrue(row["target_kind"])

    def test_zurich_frozen_coordinates(self):
        rows = [r for r in self.records if r["event_id"].startswith("Z")]
        self.assertEqual(len(rows), 10)
        for row in rows:
            self.assertEqual(row["annotation_image"]["sha256"], build.ZURICH_SHA)
            self.assertEqual((row["annotation_image"]["width"], row["annotation_image"]["height"]), (1538, 1754))
            self.assertTrue(row["prior_prediction_exposure"])
            self.assertTrue(row["requires_map_version_review"])

    def test_hypotheses_remain_distinct(self):
        rows = [r for r in self.records if r["status"] == "ambiguous" and r["geometry"]]
        self.assertEqual(len(rows), 3)  # 2026-10-21: one hypothesis item was replaced by a verbatim-source question
        self.assertTrue(all(r["geometry_semantics"] == "hypothesis_only" for r in rows))

    def test_source_conflicts_have_no_geometry(self):
        rows = [r for r in self.records if r["status"] == "source_conflict"]
        # 2026-10-21: MF0045/MF0083/MF0095 were rewritten from Petre's text, so no source conflict remains.
        self.assertEqual({r["event_id"] for r in rows}, set())
        self.assertTrue(all(r["geometry"] is None for r in rows))

    def test_reject_out_of_bounds(self):
        row = copy.deepcopy(self.records[0])
        row["geometry"]["coordinates"][0] = [1538, 0]
        with self.assertRaisesRegex(ValueError, "Out of bounds"):
            build.validate_decision(row, 1538, 1754)

    def test_reject_self_intersections(self):
        row = copy.deepcopy(self.records[0])
        row["geometry"] = {"type": "polygon", "coordinates": [[10, 10], [60, 50], [10, 60], [50, 10]]}
        with self.assertRaisesRegex(ValueError, "Self-intersecting"):
            build.validate_decision(row, 100, 100)

    def test_reject_collinear_polygon(self):
        row = copy.deepcopy(self.records[0])
        row["geometry"] = {"type": "polygon", "coordinates": [[10, 10], [20, 20], [30, 30]]}
        with self.assertRaisesRegex(ValueError, "Zero area"):
            build.validate_decision(row, 100, 100)

    def test_reject_null_proposed(self):
        row = copy.deepcopy(self.records[0])
        row.update(status="proposed", geometry=None)
        with self.assertRaisesRegex(ValueError, "Proposed without"):
            build.validate_decision(row, 100, 100)

    def test_source_review_covers_known_events_only(self):
        ids = {r["event_id"] for r in self.records}
        review = build.source_review(ids)
        self.assertEqual(len([e for e in review if "screening" in review[e]]), 139)
        for event_id, info in review.items():
            original = info.get("original")
            if original and original["extracted"]:
                self.assertTrue(original["original_text"].strip(), event_id)
                if original["language"] != "en":
                    self.assertTrue(original["english_translation"], event_id)
        with self.assertRaisesRegex(ValueError, "unknown events"):
            build.source_review(ids - {"MF0009"})

    def test_display_translations_cover_shown_notes(self):
        review = build.source_review({r["event_id"] for r in self.records}, build.text_first_ids(self.records))
        table, missing = build.display_translations(self.records, review)
        self.assertEqual(missing, [])
        for zh, en in table.items():
            self.assertTrue(en.strip(), zh)
            self.assertIsNone(build.HAN.search(en), zh)

    def test_all_generated_overviews_keep_native_dimensions(self):
        for name in {r["annotation_image"]["path"] for r in self.records}:
            with build.Image.open(build.HERE / "overviews" / f"{Path(name).stem}.png") as image:
                self.assertEqual(image.size, (self.assets[name]["width"], self.assets[name]["height"]))


if __name__ == "__main__":
    unittest.main()
