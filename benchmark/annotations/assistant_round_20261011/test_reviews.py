import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest

from serve_reviews import Conflict, ReviewStore, make_server


HERE = Path(__file__).resolve().parent


class ReviewTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for name in ("annotations.jsonl", "manifest.json"):
            (self.root / name).write_bytes((HERE / name).read_bytes())
        self.store = ReviewStore(self.root)
        self.body = {"event_id": "MF0013", "decision": "accepted", "notes": "Checked text and suburb boundary.",
                     "reviewer": "Test reviewer", "revision": 0,
                     "candidate_sha256": self.store.versions["MF0013"]}

    def tearDown(self):
        self.temp.cleanup()

    def test_store_does_not_create_reviews_until_saved(self):
        self.assertEqual(self.store.catalog()["reviews"], {})
        self.assertFalse(self.store.journal.exists())

    def test_persist_restart_and_revise(self):
        source = self.store.source.read_bytes()
        first = self.store.save(self.body)
        self.assertEqual(first["revision"], 1)
        restarted = ReviewStore(self.root)
        self.assertEqual(restarted.catalog()["reviews"]["MF0013"], first)
        changed = {**self.body, "revision": 1, "decision": "needs_changes", "notes": "Shorten the north edge."}
        second = restarted.save(changed)
        self.assertEqual(second["revision"], 2)
        self.assertEqual(len(self.store.journal.read_text().splitlines()), 2)
        self.assertEqual(self.store.source.read_bytes(), source)
        self.assertFalse(second["eligible_for_scoring"])

    def test_stale_revision_rejected(self):
        self.store.save(self.body)
        with self.assertRaises(Conflict):
            ReviewStore(self.root).save(self.body)
        self.assertEqual(len(self.store.journal.read_text().splitlines()), 1)

    def test_stale_candidate_rejected(self):
        with self.assertRaises(Conflict):
            self.store.save({**self.body, "candidate_sha256": "old"})
        self.assertFalse(self.store.journal.exists())

    def test_null_geometry_cannot_be_accepted(self):
        with self.assertRaisesRegex(ValueError, "no geometry"):
            self.store.save({**self.body, "event_id": "Z0003", "candidate_sha256": self.store.versions["Z0003"]})

    def test_no_location_confirms_abstention_item(self):
        body = {**self.body, "event_id": "Z0003", "decision": "accepted_no_location", "notes": "",
                "candidate_sha256": self.store.versions["Z0003"]}
        record = self.store.save(body)
        self.assertEqual(record["decision"], "accepted_no_location")
        self.assertIsNone(record["human_geometry"])

    def test_no_location_requires_cleared_geometry(self):
        body = {**self.body, "decision": "accepted_no_location", "notes": "Village lies off the sheet."}
        with self.assertRaisesRegex(ValueError, "Clear the geometry"):
            self.store.save(body)
        self.assertEqual(self.store.catalog()["reviews"], {})
        cleared = self.store.save({**body, "human_geometry": None, "image_sha256": self.store.records["MF0013"]["annotation_image"]["sha256"]})
        self.assertEqual(cleared["geometry_source"], "human_edit")
        self.assertIsNone(cleared["human_geometry"])

    def test_no_location_needs_reason_unless_candidate_was_outside_map(self):
        body = {**self.body, "decision": "accepted_no_location", "notes": "", "human_geometry": None,
                "image_sha256": self.store.records["MF0013"]["annotation_image"]["sha256"]}
        with self.assertRaisesRegex(ValueError, "cannot be marked"):
            self.store.save(body)

    def test_required_review_fields(self):
        for patch in [{"reviewer": " "}, {"reviewer": []}, {"notes": []}, {"decision": "wrong"}, {"revision": True},
                      {"decision": "needs_changes", "notes": ""}, {"decision": "needs_evidence", "notes": ""},
                      {"decision": "rejected", "notes": ""}, {"event_id": []}]:
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                self.store.save({**self.body, **patch})

    def test_ambiguous_acceptance_requires_reason(self):
        body = {**self.body, "event_id": "Z0001", "notes": "", "candidate_sha256": self.store.versions["Z0001"]}
        with self.assertRaisesRegex(ValueError, "uncertainty"):
            self.store.save(body)
        self.assertEqual(self.store.save({**body, "notes": "Independent bank evidence checked."})["decision"], "accepted")

    def test_reset_is_a_history_entry(self):
        self.store.save(self.body)
        self.store.save({**self.body, "revision": 1, "decision": "pending"})
        self.assertEqual(self.store.catalog()["reviews"]["MF0013"]["decision"], "pending")
        self.assertEqual(len(self.store.journal.read_text().splitlines()), 2)

    def test_source_changed_while_running_is_rejected(self):
        self.store.source.write_text("{}\n", encoding="utf-8")
        with self.assertRaises(Conflict):
            self.store.save(self.body)

    def modified_body(self, geometry=None):
        return {**self.body, "decision": "modified_accepted", "notes": "Corrected against source map.",
                "human_geometry": geometry or {"type": "point", "coordinates": [[100, 150]]},
                "image_sha256": self.store.records["MF0013"]["annotation_image"]["sha256"]}

    def test_modified_geometry_survives_restart_without_changing_candidate(self):
        before = self.store.source.read_bytes()
        body = self.modified_body()
        saved = self.store.save(body)
        self.assertEqual(saved["human_geometry"], body["human_geometry"])
        self.assertEqual(saved["geometry_source"], "human_edit")
        self.assertEqual(saved["schema_version"], 2)
        self.assertFalse(saved["eligible_for_scoring"])
        self.assertEqual(ReviewStore(self.root).catalog()["reviews"]["MF0013"], saved)
        self.assertEqual(self.store.source.read_bytes(), before)

    def test_legacy_request_preserves_existing_geometry(self):
        saved = self.store.save(self.modified_body())
        updated = self.store.save({**self.body, "revision": 1, "decision": "needs_changes"})
        self.assertEqual(updated["human_geometry"], saved["human_geometry"])

    def test_geometry_acceptance_rules(self):
        for body in [self.modified_body() | {"notes": ""},
                     self.modified_body() | {"decision": "accepted"},
                     self.modified_body() | {"human_geometry": None},
                     self.modified_body(self.store.records["MF0013"]["geometry"])]:
            with self.subTest(body=body), self.assertRaises(ValueError):
                self.store.save(body)

    def test_wrong_image_version_is_conflict(self):
        with self.assertRaises(Conflict):
            self.store.save(self.modified_body() | {"image_sha256": "wrong"})

    def test_invalid_geometry_rejected(self):
        cases = [
            {"type": "point", "coordinates": [[-1, 20]]},
            {"type": "point", "coordinates": [[99999, 20]]},
            {"type": "point", "coordinates": [[float("nan"), 20]]},
            {"type": "point", "coordinates": [[True, 20]]},
            {"type": "line", "coordinates": [[10, 10]]},
            {"type": "polygon", "coordinates": [[10,10],[100,100],[10,100],[100,10]]},
            {"type": "polygon", "coordinates": [[10,10],[20,20],[30,30]]},
            {"type": "polygon", "coordinates": [[10,10],[20,10],[20,10]]},
        ]
        for geometry in cases:
            with self.subTest(geometry=geometry), self.assertRaises(ValueError):
                self.store.save(self.modified_body(geometry))

    def test_new_geometry_for_empty_candidate(self):
        body = self.modified_body() | {"event_id": "Z0003", "candidate_sha256": self.store.versions["Z0003"],
            "image_sha256": self.store.records["Z0003"]["annotation_image"]["sha256"]}
        saved = self.store.save(body)
        self.assertEqual(saved["candidate_status"], "outside_map")
        self.assertEqual(saved["decision"], "modified_accepted")

    def test_clear_and_restore_are_append_only(self):
        self.store.save(self.modified_body())
        cleared = self.store.save(self.modified_body() | {"revision": 1, "decision": "needs_changes", "human_geometry": None})
        self.assertIsNone(cleared["human_geometry"])
        restored = self.store.save(self.modified_body() | {"revision": 2, "decision": "accepted",
                                   "human_geometry": self.store.records["MF0013"]["geometry"]})
        self.assertEqual(restored["geometry_source"], "ai_candidate")
        self.assertEqual(len(self.store.journal.read_text().splitlines()), 3)


class HTTPReviewTest(ReviewTest):
    def setUp(self):
        super().setUp()
        self.server = make_server(self.root, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_address[1]

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        super().tearDown()

    def request(self, method, path, body=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.port)
        conn.request(method, path, json.dumps(body) if body is not None else None, headers or {})
        response = conn.getresponse()
        status, data = response.status, response.read()
        conn.close()
        return status, json.loads(data)

    def auth(self):
        return {"Content-Type": "application/json", "X-CSRF-Token": self.server.token, "Origin": f"http://127.0.0.1:{self.port}"}

    def test_http_save_and_export(self):
        status, catalog = self.request("GET", "/api/reviews")
        self.assertEqual(status, 200)
        self.assertEqual(catalog["csrf"], self.server.token)
        status, result = self.request("POST", "/api/reviews", self.body, self.auth())
        self.assertEqual(status, 200)
        self.assertEqual(result["review"]["decision"], "accepted")
        status, exported = self.request("GET", "/api/reviews/export")
        self.assertEqual(status, 200)
        self.assertEqual(exported["reviews"]["MF0013"]["revision"], 1)

    def test_http_geometry_roundtrip(self):
        self.assertTrue(self.request("GET", "/api/reviews")[1]["geometry_editing"])
        status, saved = self.request("POST", "/api/reviews", self.modified_body(), self.auth())
        self.assertEqual(status, 200)
        self.assertEqual(saved["review"]["geometry_source"], "human_edit")
        status, exported = self.request("GET", "/api/reviews/export")
        self.assertEqual(exported["reviews"]["MF0013"]["human_geometry"], saved["review"]["human_geometry"])

    def test_cross_origin_csrf_and_host_rejected(self):
        for patch in [{"Origin": "https://evil.example"}, {"X-CSRF-Token": "wrong"}, {"Host": "evil.example"}, {"Origin": "null"}]:
            with self.subTest(patch=patch):
                self.assertEqual(self.request("POST", "/api/reviews", self.body, {**self.auth(), **patch})[0], 403)
        self.assertFalse(self.server.store.journal.exists())

    def test_unknown_file_not_served(self):
        (self.root / ".env").write_text("TEST_SECRET=never served\n")
        for path in ["/.env", "/overviews/../../.env", "/serve_reviews.py", "/human_reviews.jsonl"]:
            self.assertEqual(self.request("GET", path)[0], 404)

    def test_stale_http_revision_returns_conflict(self):
        self.assertEqual(self.request("POST", "/api/reviews", self.body, self.auth())[0], 200)
        self.assertEqual(self.request("POST", "/api/reviews", self.body, self.auth())[0], 409)

    def test_public_origin_behind_proxy(self):
        self.server.public_origin = "https://experiment.chanlukaka.com"
        headers = {**self.auth(), "Host": "experiment.chanlukaka.com", "Origin": self.server.public_origin}
        self.assertEqual(self.request("GET", "/api/reviews", headers=headers)[0], 200)
        for patch in [{"Origin": "http://experiment.chanlukaka.com"}, {"Origin": "null"},
                      {"Host": "evil.example"}, {"X-CSRF-Token": "wrong"}]:
            self.assertEqual(self.request("POST", "/api/reviews", self.body, headers | patch)[0], 403)
        self.assertEqual(self.request("POST", "/api/reviews", self.body, headers)[0], 200)
        self.assertEqual(self.server.server_address[0], "127.0.0.1")

    def test_web_asset_allowlist(self):
        (self.root / "images").mkdir()
        (self.root / "images/test.png").write_bytes(b"test")
        self.assertEqual(self.request("GET", "/images/test.png")[0], 404)
        self.server.store.manifest["web_assets"] = ["images/test.png"]
        conn = http.client.HTTPConnection("127.0.0.1", self.port)
        conn.request("GET", "/images/test.png")
        response = conn.getresponse()
        self.assertEqual(response.status, 200)
        self.assertEqual(response.read(), b"test")
        conn.close()


if __name__ == "__main__":
    unittest.main()
