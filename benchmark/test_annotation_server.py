import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace

from PIL import Image

from annotation_server import Conflict, DATASETS, ROOT, Store, workspace_info


class AnnotationServerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "benchmark").mkdir()
        (self.root / "maps").mkdir()
        Image.new("RGB", (100, 80), "white").save(self.root / "maps/test.png")
        for i, (source, _) in enumerate(DATASETS):
            rec = {"event_id": ["N0001", "Z0001"][i],
                   "battle_id": ["borkowo", "zurich_second_1799"][i],
                   "image": "maps/test.png", "event_text": "Source text", "target_question": "Where?"}
            (self.root / source).write_text(json.dumps(rec) + "\n")
        self.store = Store(self.root)

    def payload(self, **updates):
        return {"base_revision": None, "status": "accepted", "evidence": "Test-only evidence",
                "annotator": "tester", "geo_feature_type": "bridge", "tolerance_px": 3,
                "geometry": {"type": "point", "coordinates": [[20, 30]]}, **updates}

    def test_catalog_unifies_files_and_uses_actual_image_dimensions(self):
        self.assertEqual(sum(b["total"] for b in self.store.catalog()["battles"]), 2)
        self.assertEqual(self.store.event("Z0001")["dimensions"], (100, 80))

    def test_workspace_navigation_keeps_datasets_separate(self):
        main = workspace_info(SimpleNamespace(root=ROOT, records={"N1": {}}), 8801, 8802)
        self.assertEqual(main["events_url"], "/")
        self.assertEqual(main["place_lab_url"], "http://127.0.0.1:8802/place-lab.html")
        self.assertEqual(main["kind"], "main")
        isolated = workspace_info(SimpleNamespace(root=self.root, records={"P1": {"place_name": "Zurich"}}), 8801, 8802)
        self.assertEqual(isolated["name"], "地名实验工作区")
        self.assertEqual(isolated["item_label"], "地名样本")
        self.assertEqual(isolated["events_url"], "http://127.0.0.1:8801/")
        self.assertEqual(isolated["place_lab_url"], "/place-lab.html")
        with self.assertRaises(ValueError):
            workspace_info(self.store, event_port=0)

    def test_roundtrip_and_append_only_revisions(self):
        first = self.store.save("N0001", self.payload())
        second = self.store.save("N0001", self.payload(base_revision=first["revision"], evidence="Revised"))
        self.assertEqual(second["annotation"]["geo_gold_px"], [20, 30])
        self.assertEqual(second["annotation"]["event_text"], "Source text")
        self.assertEqual(second["annotation"]["img_w"], 100)
        self.assertEqual(len(second["history"]), 2)
        self.assertEqual(second["history"][1]["evidence"], "Test-only evidence")
        self.assertEqual(Store(self.root).event("N0001")["annotation"]["evidence"], "Revised")

    def test_saves_to_original_dataset_output(self):
        self.store.save("Z0001", self.payload())
        self.assertTrue((self.root / DATASETS[1][1]).exists())
        self.assertFalse((self.root / DATASETS[0][1]).exists())

    def test_stale_revision_does_not_overwrite(self):
        self.store.save("N0001", self.payload())
        with self.assertRaises(Conflict):
            self.store.save("N0001", self.payload())
        self.assertEqual(len(self.store.history("N0001")), 1)

    def test_required_fields(self):
        for change in ({"evidence": " "}, {"annotator": ""}, {"geo_feature_type": "camp"},
                       {"status": "pending"}, {"geometry": None}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.store.save("N0001", self.payload(**change))

    def test_invalid_geometry(self):
        for geometry in (
            {"type": "point", "coordinates": [[100, 0]]},
            {"type": "point", "coordinates": [[float("nan"), 0]]},
            {"type": "point", "coordinates": [[True, 0]]},
            {"type": "point", "coordinates": [[0, 0], [1, 1]]},
            {"type": "line", "coordinates": [[0, 0]]},
            {"type": "polygon", "coordinates": [[0, 0], [20, 20], [0, 20], [20, 0]]},
        ):
            with self.subTest(geometry=geometry), self.assertRaises(ValueError):
                self.store.save("N0001", self.payload(geometry=geometry))

    def test_polygon_has_no_point_or_tolerance(self):
        result = self.store.save("N0001", self.payload(geometry={"type": "polygon", "coordinates": [[10, 10], [30, 10], [30, 30]]}))
        self.assertIsNone(result["annotation"]["geo_gold_px"])
        self.assertIsNone(result["annotation"]["tolerance_px"])

    def test_unlocatable_can_have_no_geometry(self):
        result = self.store.save("Z0001", self.payload(status="unlocatable", geometry=None))
        self.assertIsNone(result["annotation"]["geometry"])
        self.assertEqual(result["annotation"]["gold_status"], "not_accepted")

    def test_invalid_tolerance(self):
        for value in (-1, float("inf"), 101, "5"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.store.save("N0001", self.payload(tolerance_px=value))

    def test_unknown_event_cannot_write(self):
        with self.assertRaises(KeyError):
            self.store.save("../../.env", self.payload())


if __name__ == "__main__":
    unittest.main()
