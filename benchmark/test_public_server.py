"""HTTP regression tests for the authenticated reverse-proxy deployment."""
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest

from PIL import Image
from annotation_server import DATASETS, make_server


class PublicServerTests(unittest.TestCase):
    origin = "https://experiment.chanlukaka.com"

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        (root / "benchmark").mkdir()
        (root / "maps").mkdir()
        Image.new("RGB", (100, 80), "white").save(root / "maps/test.png")
        for i, (source, _) in enumerate(DATASETS):
            row = {"event_id": f"T{i}", "battle_id": "zurich_second_1799",
                   "image": "maps/test.png", "event_text": "Fixture", "target_question": "Where?"}
            (root / source).write_text(json.dumps(row) + "\n")
        self.root = root
        self.server = make_server(0, root, public_origin=self.origin, url_prefix="/labels",
                                  events_url="/", place_lab_url="/labels/place-lab.html")
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop)

    def stop(self):
        self.server.shutdown()
        self.server.place_jobs.close()
        self.server.server_close()
        self.thread.join()

    def request(self, method, path, data=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        values = {"Host": "experiment.chanlukaka.com", **(headers or {})}
        conn.request(method, path, json.dumps(data) if data is not None else None, values)
        response = conn.getresponse()
        result = response.status, response.read()
        conn.close()
        return result

    def test_host_and_html_mount(self):
        status, html = self.request("GET", "/atlas.html")
        self.assertEqual(status, 200)
        self.assertIn(b'<base href="/labels/">', html)
        self.assertEqual(self.request("GET", "/", headers={"Host": "evil.example"})[0], 403)
        self.assertEqual(self.request("GET", "/", headers={"Host": "127.0.0.1:8767"})[0], 403)

    def test_public_navigation_has_no_loopback_links(self):
        status, data = self.request("GET", "/api/catalog")
        self.assertEqual(status, 200)
        workspace = json.loads(data)["workspace"]
        self.assertEqual(workspace["events_url"], "/")
        self.assertEqual(workspace["place_lab_url"], "/labels/place-lab.html")

    def test_https_save_and_csrf(self):
        body = {"base_revision": None, "status": "unlocatable", "evidence": "Fixture",
                "annotator": "test", "geo_feature_type": "other", "geometry": None}
        headers = {"Origin": self.origin, "X-CSRF-Token": self.server.token}
        for origin in ("http://experiment.chanlukaka.com", "https://evil.example", "null"):
            self.assertEqual(self.request("POST", "/api/event/T0", body,
                                          {**headers, "Origin": origin})[0], 403)
        self.assertEqual(self.request("POST", "/api/event/T0", body,
                                      {"X-CSRF-Token": self.server.token})[0], 403)
        self.assertEqual(self.request("POST", "/api/event/T0", body,
                                      {**headers, "X-CSRF-Token": "bad"})[0], 403)
        self.assertEqual(self.request("POST", "/api/event/T0", body, headers)[0], 200)
        self.assertEqual(self.request("POST", "/api/event/T0", body, headers)[0], 409)

    def test_no_inference_or_private_files(self):
        headers = {"Origin": self.origin, "X-CSRF-Token": self.server.token}
        self.assertEqual(self.request("POST", "/api/atlas/test/place-predict", {}, headers)[0], 403)
        for path in ("/.env", "/.git/config", "/../annotation_server.py", "/%2e%2e/annotation_server.py"):
            self.assertEqual(self.request("GET", path)[0], 404)

    def test_invalid_configuration(self):
        for kwargs in ({"public_origin": "http://example.org"},
                       {"public_origin": "https://example.org/path"},
                       {"url_prefix": '/x\" onload=\"bad'},
                       {"events_url": "//evil.example"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                make_server(0, self.root, **kwargs)


if __name__ == "__main__":
    unittest.main()
