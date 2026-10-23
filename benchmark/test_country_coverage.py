import hashlib
import json
import unittest

from annotate_geo import ROOT, load_jsonl
from country_coverage import coverage


class CountryCoverageTests(unittest.TestCase):
    def test_each_map_needs_four_not_just_eight_in_country(self):
        scope = {"confirmed": True, "country_basis": "present_day", "min_maps_per_country": 2,
                 "min_events_per_map": 4, "countries": [{"name": "X"}]}
        battles = [{"id": "b", "country": "X"}]
        rows = [{"event_id": str(n), "battle_id": "b", "image": "one" if n < 5 else "two"}
                for n in range(8)]
        result = coverage(rows, battles, scope)
        self.assertEqual(result["countries"][0]["qualifying_maps"], 1)
        self.assertFalse(result["complete"])
        rows[-1]["image"] = "one"
        rows[3]["image"] = "two"
        rows[4]["image"] = "two"
        self.assertTrue(coverage(rows, battles, scope)["complete"])

    def test_duplicate_download_and_unconfirmed_scope_do_not_pass(self):
        scope = {"confirmed": False, "country_basis": "present_day", "min_maps_per_country": 2,
                 "min_events_per_map": 4, "countries": [{"name": "X"}, {"name": "Y"}]}
        rows = [{"event_id": str(n), "battle_id": "b", "image": str(n), "map_asset_sha256": "same"}
                for n in range(8)]
        result = coverage(rows, [{"id": "b", "country": "X"}], scope)
        self.assertEqual(result["map_count"], 1)
        self.assertFalse(result["complete"])
        self.assertEqual(result["countries"][1]["map_count"], 0)

    def test_live_candidate_coverage_and_draft_provenance(self):
        from annotation_server import BATTLES, Store
        store = Store(ROOT)
        scope = json.loads((ROOT / "benchmark/country_scope.json").read_text())
        result = coverage(store.records.values(), BATTLES, scope)
        self.assertEqual((result["map_count"], result["event_count"]), (26, 110))
        self.assertEqual(result["countries_with_candidate_quota"], 13)
        self.assertFalse(result["complete"])
        added = [r for r in store.records.values() if r.get("dataset") == "napoleon_maps_country_expansion_v1"]
        self.assertEqual(len(added), 88)
        self.assertEqual(sum(r["evidence_tier"] == "map_derived" for r in added), 64)
        for row in added:
            self.assertEqual(hashlib.sha256((ROOT / row["image"]).read_bytes()).hexdigest(), row["map_asset_sha256"])
            self.assertEqual(row["curation_status"], "draft_needs_human_review")
            self.assertFalse(row["independent_corroboration"])
            self.assertNotIn("geometry", row)
            self.assertNotIn("geo_gold_px", row)
        self.assertEqual({r["split_group"] for r in added if r["battle_id"] == "bussaco_reynier_1810"}, {"bussaco_1810"})
        self.assertEqual({r["split_group"] for r in added if r["battle_id"] == "marengo_morning_1800"}, {"marengo_1800"})

    def test_old_candidate_prefix_is_unchanged(self):
        path = ROOT / "benchmark/map_first_candidates.jsonl"
        prefix = b"".join(path.read_bytes().splitlines(keepends=True)[:12])
        self.assertEqual(hashlib.sha256(prefix).hexdigest(),
                         "6db2a19eb0111f2b6eb9160ef99a973b2d9cc47825d01ce3547fccb52b7d1ba2")


if __name__ == "__main__":
    unittest.main()
