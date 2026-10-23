import json
from pathlib import Path
import tempfile
import unittest

from PIL import Image
from atlas_store import digest
from export_place_results import export


class ExportPlaceResultsTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.lab = Path(tmp.name)
        self.run = self.lab / "runs/test"
        self.run.mkdir(parents=True)
        Image.new("RGB", (600, 400), "white").save(self.run / "map.png")
        self.sha = digest((self.run / "map.png").read_bytes())
        meta = {"map_id": "m", "map_version": "v", "image_sha256": self.sha}
        task = {**meta, "id": "t", "place_name": "Example"}
        gold = {**meta, "task_id": "t", "geometry": {"type": "point", "coordinates": [[100, 100]]},
                "status": "accepted", "confidence": 5, "tolerance_px": 20, "created_at": "2026-09-23T10:00:00+00:00"}
        later = {**gold, "geometry": {"type": "point", "coordinates": [[500, 300]]}, "created_at": "2026-09-24T10:00:00+00:00"}
        (self.lab / "tasks.jsonl").write_text(json.dumps(task) + "\n")
        (self.lab / "gold.jsonl").write_text(json.dumps(gold) + "\n" + json.dumps(later) + "\n")
        self.state = {**meta, "job_id": "test", "batch": True, "status": "completed", "task_ids": ["t"],
            "created_at": "2026-09-23T11:00:00+00:00", "elapsed_seconds": 3,
            "counts": {"valid": 1, "abstained": 0, "error": 0}, "results": [{**meta, "task_id": "t",
            "geometry": {"type": "point", "coordinates": [[110, 100]]}}]}
        (self.run / "state.json").write_text(json.dumps(self.state))
        (self.run / "input.json").write_text(json.dumps({**meta, "model": "test-model", "coordinate_mode": "normalized_1000"}))
        (self.run / "result.json").write_text(json.dumps({"raw": "original response"}))

    def test_export_freezes_run_start_gold_and_preserves_raw_response(self):
        before = (self.lab / "gold.jsonl").read_bytes()
        path, summary = export(self.run)
        record = json.loads((path / "experiment.json").read_text())
        self.assertEqual(summary["hits_with_saved_tolerance"], 1)
        self.assertEqual(summary["mean_distance_px"], 10)
        self.assertEqual(record["raw_model_result"]["raw"], "original response")
        self.assertEqual(record["rows"][0]["gold"]["geometry"]["coordinates"], [[100, 100]])
        with Image.open(path / "comparison.png") as image:
            self.assertEqual(image.size, (1224, 590))
            self.assertEqual(image.getpixel((100, 170)), (196, 60, 72))
        self.assertEqual(before, (self.lab / "gold.jsonl").read_bytes())
        with self.assertRaises(FileExistsError):
            export(self.run)

    def test_mismatched_map_is_rejected_before_export(self):
        Image.new("RGB", (600, 400), "black").save(self.run / "map.png")
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            export(self.run)
        self.assertFalse((self.run / "review").exists())


if __name__ == "__main__":
    unittest.main()
