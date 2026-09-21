import hashlib
import json
import unittest
from html.parser import HTMLParser
from pathlib import Path

from PIL import Image
from annotate_geo import FEATURE_TYPES
from annotation_server import Store, DATASETS
from atlas_store import AtlasStore


ROOT = Path(__file__).resolve().parents[1]


class ParagraphParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paragraphs = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag == "p":
            self.current = []

    def handle_data(self, data):
        if self.current is not None:
            self.current.append(data)

    def handle_endtag(self, tag):
        if tag == "p" and self.current is not None:
            self.paragraphs.append(" ".join("".join(self.current).split()))
            self.current = None


class ZurichPilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = [json.loads(line) for line in
                       (ROOT / "benchmark/zurich_pilot_10.jsonl").read_text().splitlines()]

    def test_ten_unique_pending_candidates_without_gold(self):
        self.assertEqual({r["event_id"] for r in self.records},
                         {f"Z{i:04d}" for i in range(1, 11)})
        self.assertEqual(len(self.records), 10)
        for rec in self.records:
            self.assertEqual(rec["status"], "pending")
            self.assertEqual(rec["gold_status"], "not_annotated")
            self.assertIsNone(rec.get("geometry"))
            self.assertIsNone(rec.get("geo_gold_px"))
            self.assertEqual(rec["translation_review"], "pending")
            self.assertTrue(rec["event_text"])
            self.assertTrue(rec["target_question"])
            self.assertIn(rec["suggested_geometry"], {"point", "line", "polygon"})
            self.assertIn(rec["suggested_feature_type"], {code for code, _ in FEATURE_TYPES})

    def test_original_five_preserved_verbatim(self):
        old = (ROOT / "benchmark/zurich_pilot_5.jsonl").read_bytes()
        new = (ROOT / "benchmark/zurich_pilot_10.jsonl").read_bytes()
        self.assertTrue(new.startswith(old))

    def test_gui_loads_ten_events_on_same_reference(self):
        self.assertIn(("benchmark/zurich_pilot_10.jsonl", "benchmark/zurich_annotations.jsonl"), DATASETS)
        self.assertNotIn("benchmark/zurich_pilot_5.jsonl", {src for src, _ in DATASETS})
        atlas = AtlasStore(Store(ROOT))
        group = next(g for g in atlas.groups.values() if g["battle_id"] == "zurich_second_1799")
        expected = [r["event_id"] for r in self.records]
        self.assertEqual(group["events"], expected)
        self.assertEqual(group["id"], hashlib.sha256(self.records[0]["image"].encode()).hexdigest()[:16])
        self.assertEqual([e["id"] for e in atlas.detail(group["id"])["events"]], expected)

    def test_original_paragraphs_match_saved_source(self):
        for rec in self.records:
            parser = ParagraphParser()
            parser.feed((ROOT / rec["source_local"]).read_text(encoding="utf-8"))
            self.assertEqual(rec["source_text"],
                             parser.paragraphs[rec["source_paragraph_index"]])

    def test_map_integrity_and_dimensions(self):
        for rec in self.records:
            path = ROOT / rec["image"]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),
                             rec["map_sha256"])
            with Image.open(path) as image:
                self.assertEqual(image.size, (rec["img_w"], rec["img_h"]))
                image.verify()

    def test_shared_geography_and_context_stay_grouped(self):
        self.assertEqual({r["split_group"] for r in self.records}, {"zurich_1799"})
        self.assertEqual(len({r["context_group"] for r in self.records[:3]}), 1)
        self.assertEqual(sum(r["question_class"] == "explicit_place_control"
                             for r in self.records), 4)
        self.assertEqual(len({r["target_event"] for r in self.records}), 10)
        self.assertEqual(len({r["image"] for r in self.records}), 1)
        self.assertEqual(self.records[5]["context_group"], self.records[0]["context_group"])
        self.assertEqual(self.records[9]["source_paragraph_index"], 351)


if __name__ == "__main__":
    unittest.main()
