import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PIL import Image
from annotation_server import Store
from atlas_store import AtlasStore
from place_diagnostics import prepare, parse_point, crop_point_to_full, run, score, reparse, MODES
from run_atlas_vlm import image_preprocessing_metadata, read_package


class CoordinateTests(unittest.TestCase):
    def test_normalized_to_non_square_pixels_and_rejection(self):
        row = {"event_id": "P1", "width": 1600, "height": 800}
        def raw(x, y):
            return json.dumps({"event_id": "P1", "geometry": {"type": "point", "coordinates": [[x, y]]}})
        self.assertEqual(parse_point(raw(250, 750), row, "normalized_1000")["geometry"]["coordinates"], [[400, 600]])
        self.assertEqual(parse_point(raw(250, 750), row, "pixels")["geometry"]["coordinates"], [[250, 750]])
        for x, y in ((1001, 10), (-1, 10), (1000, 500), (500, 1000), (float("nan"), 5)):
            with self.subTest(x=x, y=y), self.assertRaises(ValueError):
                parse_point(raw(x, y), row, "normalized_1000")
        self.assertIsNone(parse_point('{"event_id":"P1","geometry":null}', row, "pixels")["geometry"])

    def test_crop_offsets_resize_and_bounds(self):
        self.assertEqual(crop_point_to_full([20, 30], [100, 200, 500, 600], [400, 400]), [120, 230])
        self.assertEqual(crop_point_to_full([20, 30], [100, 200, 500, 600], [200, 100]), [140, 320])
        for point in ([-1, 0], [400, 0], [0, 400]):
            with self.assertRaises(ValueError):
                crop_point_to_full(point, [100, 200, 500, 600], [400, 400])

    def test_flat_point_repair_is_explicit_and_does_not_guess_coordinate_mode(self):
        raw = '{"event_id":"P1","geometry":{"type":"point","coordinates":[250,750]}}'
        row = {"event_id": "P1", "width": 1600, "height": 800}
        result = parse_point(raw, row, "pixels")
        self.assertEqual(result["geometry"]["coordinates"], [[250, 750]])
        self.assertEqual(result["format_normalization"], "flat_point_to_singleton")
        self.assertEqual(parse_point(raw, row, "normalized_1000")["geometry"]["coordinates"], [[400, 600]])
        with self.assertRaises(ValueError):
            parse_point(raw.replace('250,750', '1600,750'), row, "pixels")

    def test_processed_dimensions_use_patch_not_merge_size(self):
        class SizeConfig:
            def __iter__(self):
                return iter([("longest_edge", 16777216)])
        processor = SimpleNamespace(image_processor=SimpleNamespace(patch_size=16, merge_size=2, size=SizeConfig()))
        report = image_preprocessing_metadata(processor, [2177, 1699], [[1, 106, 136]])
        self.assertEqual(report["processed_size_wh"], [2176, 1696])
        self.assertEqual(report["visual_tokens"], 3604)
        self.assertIn('16777216', json.dumps(report))


class DiagnosticTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        image = self.root / "source.png"
        Image.new("RGB", (400, 300), "white").save(image)
        self.dataset = self.root / "dataset"
        prepare(image, self.dataset)

    def test_packages_same_map_pending_gold_and_no_overwrite(self):
        packages = [read_package(self.dataset / f"full_{m}.zip") for m in MODES]
        self.assertEqual(packages[0][1:3], packages[1][1:3])
        self.assertEqual(len(packages[0][2]), 8)
        self.assertNotIn("confidence", packages[0][2][0])
        self.assertFalse((self.dataset / "workspace/benchmark/atlas/gold.jsonl").exists())
        with self.assertRaises(ValueError):
            prepare(self.root / "source.png", self.dataset)
        with patch("place_diagnostics.load_local_qwen") as load:
            run(self.dataset, self.root / "dry", "fake", 1, 64, False)
            load.assert_not_called()
            self.assertFalse((self.root / "dry").exists())

    def test_scoring_keeps_failures_in_denominator_and_missing_gold_null(self):
        output = self.root / "run"
        def respond(local, image, row, prompt, max_tokens):
            if "relative coordinates" in prompt:
                return 'invalid', {}
            return json.dumps({"event_id": row["event_id"], "geometry": {"type": "point", "coordinates": [[50, 50]]}}), {}
        with patch("place_diagnostics.load_local_qwen", return_value=(None, None, {})), patch("place_diagnostics.call_local_qwen", side_effect=respond):
            with self.assertRaises(SystemExit):
                run(self.dataset, output, "fake", 1, 64, True)
        workspace = self.dataset / "workspace"
        empty = self.root / "empty.json"
        score(workspace, output, empty)
        self.assertIsNone(json.loads(empty.read_text())["methods"]["pixels"]["all_reviewed"]["hit_rate"])
        store = AtlasStore(Store(workspace))
        mid = next(iter(store.groups))
        active = store.detail(mid)["active"]
        store.save_gold(mid, {"event_id": "P001", "map_version": active["version"], "base_revision": None,
            "status": "accepted", "geometry": {"type": "polygon", "coordinates": [[40, 40], [60, 40], [60, 60], [40, 60]]},
            "evidence": "Test label", "annotator": "test", "geo_feature_type": "other", "confidence": 5})
        scored = self.root / "scored.json"
        score(workspace, output, scored)
        report = json.loads(scored.read_text())["methods"]
        self.assertEqual(report["pixels"]["confidence_5"], {"n": 1, "hits": 1, "hit_rate": 1.0})
        self.assertEqual(report["normalized_1000"]["confidence_5"], {"n": 1, "hits": 0, "hit_rate": 0.0})
        with patch("place_diagnostics.load_local_qwen") as load:
            reparse(output, self.root / "reparsed")
            load.assert_not_called()
        self.assertEqual(json.loads((self.root / "reparsed/pixels.json").read_text()),
                         json.loads((output / "pixels.json").read_text()))


if __name__ == "__main__":
    unittest.main()
