"""Run with MPLBACKEND=Agg .venv/bin/python -m unittest discover -s benchmark -p test_annotation.py."""
import hashlib
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseEvent
from PIL import Image

from annotate_geo import ROOT, annotate_record, load_jsonl, prompt_feature_type, validate_geometry, write_revision


def click_at(fig, x, y):
    for name in ("button_press_event", "button_release_event"):
        event = MouseEvent(name, fig.canvas, x, y, button=1)
        fig.canvas.callbacks.process(name, event)


class AnnotationTests(unittest.TestCase):
    def test_feature_type_selection(self):
        for value, expected in [("7", "woodland"), (" BRIDGE ", "bridge"), ("12", "other")]:
            with self.subTest(value=value), patch("builtins.input", return_value=value), patch("builtins.print"):
                self.assertEqual(prompt_feature_type(), expected)

    def test_feature_type_invalid_input_retries(self):
        with patch("builtins.input", side_effect=["camp", "0", "13", "river_bank"]), patch("builtins.print"):
            self.assertEqual(prompt_feature_type(), "river_bank")

    def test_feature_type_review_defaults(self):
        for previous, expected in [(None, "other"), ("ford", "ford"), ("camp", "other")]:
            with self.subTest(previous=previous), patch("builtins.input", return_value=""), patch("builtins.print"):
                self.assertEqual(prompt_feature_type(previous), expected)

    def test_export_latest_accepted_geometry(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            candidates = folder / "candidates.jsonl"
            annotations = folder / "annotations.jsonl"
            output = folder / "export.jsonl"
            candidates.write_text('\n'.join(json.dumps({"event_id": key, "event_type": "war_conflict"}) for key in ("A", "B")))
            polygon = {"type": "polygon", "coordinates": [[0, 0], [10, 0], [10, 10]]}
            for row in [
                {"event_id": "A", "status": "accepted", "geometry": polygon},
                {"event_id": "A", "status": "rejected"},
                {"event_id": "B", "status": "accepted", "geometry": polygon, "evidence": "reviewed",
                 "geo_feature_type": "woodland", "geo_feature_vocab_version": 1},
            ]:
                write_revision(annotations, row)
            subprocess.run([sys.executable, str(ROOT / "benchmark/assemble_geo_benchmark.py"),
                            "--candidates", str(candidates), "--annotations", str(annotations),
                            "--output", str(output)], check=True, capture_output=True)
            rows = load_jsonl(output)
            self.assertEqual([r["event_id"] for r in rows], ["B"])
            self.assertEqual(rows[0]["geometry"], polygon)
            self.assertIsNone(rows[0]["geo_gold_px"])
            self.assertEqual(rows[0]["geo_feature_type"], "woodland")
            self.assertEqual(rows[0]["geo_feature_vocab_version"], 1)

    def test_invalid_geometries(self):
        for kind, points in [
            ("point", []), ("point", [[100, 2]]),
            ("line", [[1, 1]]), ("line", [[1, 1], [1, 1]]),
            ("polygon", [[0, 0], [10, 10], [0, 10], [10, 0]]),
            ("polygon", [[0, 0], [1, 1], [2, 2]]),
        ]:
            with self.subTest(kind=kind, points=points), self.assertRaises(ValueError):
                validate_geometry(kind, points, 100, 100)
        validate_geometry("polygon", [[0, 0], [10, 0], [10, 10], [0, 10]], 100, 100)

    def test_revision_history(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "annotations.jsonl"
            write_revision(path, {"event_id": "N1", "status": "accepted"})
            write_revision(path, {"event_id": "N1", "status": "rejected"})
            rows = load_jsonl(path)
            self.assertEqual(len(rows), 2)
            self.assertEqual({r["event_id"]: r for r in rows}["N1"]["status"], "rejected")

    def test_pilot_assets(self):
        rows = load_jsonl(ROOT / "benchmark/map_first_candidates.jsonl")
        self.assertEqual(len(rows), 100)
        self.assertEqual(len({r['event_id'] for r in rows}), 100)
        for row in rows:
            with Image.open(ROOT / row["image"]) as image:
                self.assertEqual(image.size, (row["img_w"], row["img_h"]))
                image.verify()
            self.assertNotIn("gold_px", row)
            self.assertTrue(row["target_question"] and row["article_url"])
            self.assertTrue(row["source_section"] and row["map_provenance"])
            self.assertIn("/images/military/maps/", row["map_url"])
            self.assertEqual(row["input_image_status"], "reference_only_not_eval_ready")
            self.assertEqual(row["gold_status"], "not_annotated")

    def test_bussaco_preserves_both_map_sources(self):
        rows = load_jsonl(ROOT / "benchmark/map_first_candidates.jsonl")
        rows = [r for r in rows if r["battle_id"] == "bussaco_1810"]
        self.assertEqual({r["event_id"] for r in rows}, {f"MF{i:04d}" for i in range(9, 13)})
        for row in rows:
            self.assertIn("gutenberg.org", row["map_asset_url"])
            self.assertIn("napoleon-series.org", row["map_url"])
            for path, checksum in ((row["image"], row["map_asset_sha256"]),
                                   (row["map_original_image"], row["map_original_sha256"])):
                self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), checksum)

    def test_san_sebastian_source_and_no_inherited_gold(self):
        rows = load_jsonl(ROOT / "benchmark/map_first_candidates.jsonl")
        rows = [r for r in rows if r["battle_id"] == "san_sebastian_1813"]
        self.assertEqual({r["event_id"] for r in rows}, {f"MF{i:04d}" for i in range(13, 17)})
        self.assertEqual(len({r["image"] for r in rows}), 1)
        for row in rows:
            self.assertEqual(row["split_group"], "san_sebastian_1813")
            self.assertEqual(row["map_url"], row["map_asset_url"])
            self.assertEqual(hashlib.sha256((ROOT / row["image"]).read_bytes()).hexdigest(),
                             row["map_asset_sha256"])
            self.assertNotIn("geometry", row)
            self.assertNotIn("geo_gold_px", row)
            self.assertTrue(row["source_section"] and row["annotation_caution"])

    def test_current_catalog_replaces_old_candidates_without_migrating_gold(self):
        from annotation_server import Store
        from atlas_store import AtlasStore
        store = Store(ROOT)
        self.assertEqual(len(store.records), 110)
        self.assertEqual(sum(eid.startswith("Z") for eid in store.records), 10)
        self.assertFalse(any(eid.startswith("N") for eid in store.records))
        self.assertTrue(all(f"MF{i:04d}" not in store.records for i in range(1, 5)))
        new_battles = json.loads((ROOT / "benchmark/map_expansion_battles.json").read_text())
        self.assertEqual({r["battle_id"] for r in store.records.values()},
                         {"bussaco_1810", "marengo_1800", "zurich_second_1799", "san_sebastian_1813"}
                         | {b["id"] for b in new_battles})
        catalog = AtlasStore(store).catalog()
        self.assertEqual(len(catalog["maps"]), 26)
        for group in catalog["maps"]:
            if group["battle_id"] != "zurich_second_1799":
                self.assertEqual(group["total"], 4)
                self.assertTrue(group["reference_image"].startswith("maps/napoleon_maps/"))
                detail = AtlasStore(store).detail(group["id"])
                self.assertTrue(all(e["id"].startswith("MF") for e in detail["events"]))

    def test_point_save_through_gui(self):
        rec = load_jsonl(ROOT / "benchmark/map_first_candidates.jsonl")[0]
        rec = {**rec, "suggested_geometry": "point"}

        def interact():
            fig = plt.gcf()
            fig.canvas.draw()
            x, y = fig.axes[0].transData.transform((120, 180))
            click_at(fig, x, y)
            fig.savefig("/tmp/napoleon_annotation_preview.png", dpi=110)
            x, y = fig.axes[-3].transAxes.transform((.5, .5))
            click_at(fig, x, y)

        with patch.object(plt, "show", interact), patch("builtins.input", side_effect=["Test evidence", "2", "4"]):
            action, ann = annotate_record(rec, None, 1, 20)
        self.assertEqual(action, "save")
        self.assertEqual(ann["geo_gold_px"], [120, 180])
        self.assertEqual(ann["tolerance_px"], 4)
        self.assertEqual(ann["status"], "accepted")
        self.assertEqual(ann["geo_feature_type"], "ford")
        self.assertEqual(ann["geo_feature_vocab_version"], 1)

    def test_polygon_and_empty_ambiguity(self):
        rec = load_jsonl(ROOT / "benchmark/map_first_candidates.jsonl")[0]
        for ambiguous in (False, True):
            def interact():
                fig = plt.gcf()
                fig.canvas.draw()
                radio_ax = fig.axes[3 if ambiguous else 2]
                label = "ambiguous" if ambiguous else "polygon"
                target = next(t for t in radio_ax.texts if t.get_text() == label)
                x, y = radio_ax.transAxes.transform((.15, target.get_position()[1]))
                click_at(fig, x, y)
                if not ambiguous:
                    for p in [(50, 50), (100, 50), (100, 100)]:
                        click_at(fig, *fig.axes[0].transData.transform(p))
                click_at(fig, *fig.axes[-3].transAxes.transform((.5, .5)))
            with patch.object(plt, "show", interact), patch("builtins.input", side_effect=["Evidence", "other"]):
                action, ann = annotate_record(rec, None, 1, 20)
            self.assertEqual(action, "save")
            self.assertIsNone(ann["geo_gold_px"])
            if ambiguous:
                self.assertEqual(ann["status"], "ambiguous")
                self.assertIsNone(ann["geometry"])
            else:
                self.assertEqual(ann["geometry"]["type"], "polygon")
                self.assertEqual(len(ann["geometry"]["coordinates"]), 3)


if __name__ == "__main__":
    unittest.main()
