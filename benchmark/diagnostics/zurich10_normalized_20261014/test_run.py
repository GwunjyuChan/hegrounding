import json
import unittest

from run import NEW_COORDINATES, OLD_COORDINATES, normalized_instruction, parse_normalized


class NormalizedEventTests(unittest.TestCase):
    row = {"event_id": "Z0004", "width": 1538, "height": 1754}

    def parse(self, geometry, event_id="Z0004"):
        return parse_normalized(json.dumps({"event_id": event_id, "geometry": geometry}), self.row, (1568, 1760))

    def test_actual_canvas_dimensions(self):
        p = self.parse({"type": "point", "coordinates": [[550, 148]]})["geometry"]["coordinates"][0]
        self.assertAlmostEqual(p[0], 862.4)
        self.assertAlmostEqual(p[1], 260.48)

    def test_null_preserved(self):
        self.assertIsNone(self.parse(None)["geometry"])

    def test_line_and_polygon_preserved(self):
        for kind, points in (("line", [[100, 100], [300, 200]]),
                             ("polygon", [[100, 100], [300, 100], [200, 300]])):
            geometry = self.parse({"type": kind, "coordinates": points})["geometry"]
            self.assertEqual(geometry["type"], kind)
            self.assertEqual(len(geometry["coordinates"]), len(points))

    def test_bounds_and_padding_rejected(self):
        for point in ([1000, 100], [990, 100], [100, 999], [-1, 100], [1001, 100], [1000.5, 100]):
            with self.subTest(point=point), self.assertRaises(ValueError):
                self.parse({"type": "point", "coordinates": [point]})

    def test_flat_point_not_repaired(self):
        with self.assertRaises(ValueError):
            self.parse({"type": "point", "coordinates": [550, 148]})

    def test_wrong_event_rejected(self):
        with self.assertRaises(ValueError):
            self.parse(None, "Z9999")

    def test_prompt_changes_only_coordinates(self):
        self.assertEqual(normalized_instruction("Before. " + OLD_COORDINATES + " After."),
                         "Before. " + NEW_COORDINATES + " After.")
        with self.assertRaises(ValueError):
            normalized_instruction("Missing coordinate contract")


if __name__ == "__main__":
    unittest.main()
