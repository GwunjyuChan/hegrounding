import unittest

from run import NAMES, TILES, build_calls, convert_point, parse_answer
from report import box_distance, label_metric, local_box, reconstruct_tiles
from run_single import calls as single_calls, parse_single


class IsolationTests(unittest.TestCase):
    def test_non_square_conversion(self):
        self.assertEqual(convert_point([500, 250], 1568, 1760, "normalized_1000"), [784, 440])
        self.assertEqual(convert_point([500, 250], 1568, 1760, "pixels"), [500, 250])

    def test_invalid_coordinates_not_repaired(self):
        for p in ([1001, 20], [-1, 20], [True, 20], [float("nan"), 20]):
            with self.assertRaises(ValueError):
                convert_point(p, 1568, 1760, "normalized_1000")
        with self.assertRaises(ValueError):
            convert_point([1000, 500], 1568, 1760, "normalized_1000")

    def test_null_is_preserved(self):
        self.assertIsNone(convert_point(None, 1568, 1760, "normalized_1000"))

    def test_tiles_partition_canvas(self):
        self.assertEqual(sum((x1-x0)*(y1-y0) for x0,y0,x1,y1 in TILES.values()), 1568*1760)
        for box in TILES.values():
            self.assertTrue(all(v % 32 == 0 for v in box))

    def test_fixed_matrix(self):
        calls = build_calls()
        self.assertEqual(len(calls), 16)
        self.assertEqual(len({c["id"] for c in calls}), 16)
        self.assertEqual(sum(c["kind"] == "text" for c in calls), 2)
        for c in calls:
            if c["kind"] == "text":
                self.assertIsNone(c["image"])

    def test_mode_pair_changes_only_coordinate_instruction(self):
        calls = {c["id"]: c for c in build_calls()}
        for seed in (0, 1):
            a = calls[f"labels_full_pixels_s{seed}"]
            b = calls[f"labels_full_normalized_1000_s{seed}"]
            self.assertEqual(a["user"], b["user"])
            self.assertEqual(a["image"], b["image"])
            self.assertEqual(a["seed"], b["seed"])

    def test_label_schema_checks_names(self):
        c = next(c for c in build_calls() if c["kind"] == "labels")
        import json
        labels = [{"name": name, "point": None} for name in NAMES]
        self.assertEqual(parse_answer(json.dumps({"labels": labels}), c)["labels"], labels)
        labels[-1]["name"] = NAMES[0]
        with self.assertRaises(ValueError):
            parse_answer(json.dumps({"labels": labels}), c)

    def test_reference_box_distance(self):
        self.assertEqual(box_distance([15, 15], [10, 10, 20, 20]), 0)
        self.assertEqual(box_distance([23, 24], [10, 10, 20, 20]), 5)

    def test_tile_reference_requires_complete_label(self):
        self.assertEqual(local_box([836, 247, 952, 284], TILES["TR"]), [36, 247, 152, 284])
        self.assertIsNone(local_box([836, 247, 952, 284], TILES["TL"]))
        self.assertIsNone(local_box([790, 100, 820, 130], TILES["TL"]))

    def test_missing_point_has_no_distance(self):
        result = label_metric(None, [10, 10, 20, 20])
        self.assertTrue(result["abstained"])
        self.assertNotIn("center_error_px", result)
        self.assertTrue(label_metric(None, None)["correct_abstention"])

    def test_tile_reconstruction_never_selects_best_candidate(self):
        rows = {f"labels_tile_{tile}": {name: {"point": None} for name in NAMES} for tile in TILES}
        rows["labels_tile_TR"]["Altstetten"]["point"] = [94, 265]
        result = reconstruct_tiles(rows)
        self.assertEqual(result["Altstetten"]["status"], "unique")
        self.assertEqual(result["Altstetten"]["candidates"][0]["point"], [894, 265])
        rows["labels_tile_TL"]["Altstetten"]["point"] = [5, 5]
        self.assertEqual(reconstruct_tiles(rows)["Altstetten"]["status"], "ambiguous")
        rows["labels_tile_BL"]["Altstetten"] = {"error_type": "IncompleteThinking"}
        self.assertEqual(reconstruct_tiles(rows)["Altstetten"]["status"], "incomplete")

    def test_single_followup_changes_only_requested_names(self):
        original = {c["id"]: c for c in build_calls()}
        followup = single_calls()
        self.assertEqual(len(followup), 12)
        for c in followup:
            before = original[c["id"].removeprefix("single_")]
            self.assertEqual(c["system"], before["system"])
            self.assertEqual(c["image"], before["image"])
            if c["kind"] == "labels":
                self.assertEqual(c["user"], {**before["user"], "names": ["Altstetten"]})

    def test_single_label_conversion(self):
        c = single_calls()[0]
        result = parse_single('{"labels":[{"name":"Altstetten","point":[500,250]}]}', c)
        self.assertEqual(result["labels"][0]["point"], [784, 440])


if __name__ == "__main__":
    unittest.main()
