import json
import unittest

from PIL import Image
from run_atlas_vlm import pad_image_without_resampling, parse_geometry


class NativePixelTests(unittest.TestCase):
    def test_padding_preserves_every_pixel_and_origin(self):
        image = Image.frombytes("RGB", (53, 71), bytes(i % 256 for i in range(53 * 71 * 3)))
        padded, metadata = pad_image_without_resampling(image, 32)
        self.assertEqual(padded.size, (64, 96))
        self.assertEqual(padded.crop((0, 0, 53, 71)).tobytes(), image.tobytes())
        self.assertEqual(padded.getpixel((53, 0)), (255, 255, 255))
        self.assertEqual(padded.getpixel((0, 71)), (255, 255, 255))
        self.assertEqual(metadata["padding_ltrb"], [0, 0, 11, 25])
        self.assertEqual(metadata["content_scale_xy"], [1.0, 1.0])
        self.assertTrue(metadata["original_pixels_verified"])

    def test_aligned_image_is_unchanged(self):
        image = Image.new("RGB", (64, 96), "red")
        padded, metadata = pad_image_without_resampling(image, 32)
        self.assertEqual(padded.tobytes(), image.tobytes())
        self.assertEqual(metadata["padding_ltrb"], [0, 0, 0, 0])

    def test_padding_is_not_a_valid_answer_region(self):
        row = {"event_id": "test", "width": 53, "height": 71}
        raw = json.dumps({"event_id": "test", "geometry": {"type": "point", "coordinates": [[54, 20]]}})
        with self.assertRaises(ValueError):
            parse_geometry(raw, row)


if __name__ == "__main__":
    unittest.main()
