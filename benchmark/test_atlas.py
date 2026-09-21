import hashlib
import io
import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import zipfile
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PIL import Image
from annotation_server import Store, DATASETS, Conflict, make_server
from atlas_store import AtlasStore
from run_atlas_vlm import read_package, parse_geometry, call_model
import run_atlas_vlm


class AtlasTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "benchmark").mkdir()
        (self.root / "maps").mkdir()
        Image.new("RGB", (300, 200), "white").save(self.root / "maps/ref.png")
        for i, (source, _) in enumerate(DATASETS):
            rows = [{"event_id": f"{i}-{j}", "battle_id": "zurich_second_1799", "image": "maps/ref.png",
                     "event_text": "The unit crossed the river.", "target_question": "Where did it land?",
                     "annotation_caution": "SECRET CAUTION", "place": "SECRET PLACE"} for j in range(2)]
            (self.root / source).write_text("\n".join(json.dumps(r) for r in rows))
        self.store = AtlasStore(Store(self.root))
        self.mid = next(iter(self.store.groups))
        buf = io.BytesIO()
        im = Image.new("RGB", (500, 400), "#ecdac5")
        im.putpixel((120, 130), (0, 0, 0))
        im.save(buf, format="PNG")
        self.source = self.store.import_source(buf.getvalue(), "input.png")
        self.map_body = {"base_revision": None, "source_id": self.source["id"], "crop": [100, 100, 400, 350],
                         "rotation": 0, "max_side": 3200, "title": "Test map", "provenance": "Test only"}
        self.current = self.store.save_map(self.mid, self.map_body)

    def gold_body(self, **changes):
        return {"event_id": "0-0", "map_version": self.current["active"]["version"], "base_revision": None,
                "status": "accepted", "geometry": {"type": "point", "coordinates": [[20, 30]]},
                "evidence": "SECRET EVIDENCE", "annotator": "test", "geo_feature_type": "river_bank",
                "tolerance_px": 5, **changes}

    def test_one_reference_has_multiple_events_and_one_active_map(self):
        self.assertEqual(len(self.store.catalog()["maps"]), 1)
        self.assertEqual(len(self.current["events"]), 4)
        self.assertEqual((self.current["active"]["width"], self.current["active"]["height"]), (300, 250))
        with Image.open(self.store.asset_path(self.current["active"]["version"])) as im:
            self.assertEqual(im.getpixel((20, 30)), (0, 0, 0))

    def test_gold_never_modifies_clean_image_or_legacy_annotations(self):
        path = self.store.asset_path(self.current["active"]["version"])
        before = path.read_bytes()
        result = self.store.save_gold(self.mid, self.gold_body())
        self.assertEqual(result["events"][0]["gold"]["geometry"]["coordinates"], [[20, 30]])
        self.assertEqual(path.read_bytes(), before)
        for _, output in DATASETS:
            self.assertFalse((self.root / output).exists())
        overlay = self.store.overlay(self.mid, "0-0", "gold")
        self.assertNotEqual(overlay, before)
        self.assertEqual(path.read_bytes(), before)

    def test_version_change_invalidates_gold_and_restore_recovers(self):
        old_version = self.current["active"]["version"]
        self.store.save_gold(self.mid, self.gold_body())
        new = self.store.save_map(self.mid, {**self.map_body, "base_revision": self.current["revision"], "crop": [80, 100, 400, 350]})
        self.assertNotEqual(old_version, new["active"]["version"])
        self.assertIsNone(new["events"][0]["gold"])
        with self.assertRaises(Conflict):
            self.store.save_gold(self.mid, self.gold_body())
        restored = self.store.restore(self.mid, {"base_revision": new["revision"], "version": old_version})
        self.assertIsNotNone(restored["events"][0]["gold"])

    def test_conflicts_and_revision_persistence(self):
        first = self.store.save_gold(self.mid, self.gold_body())
        with self.assertRaises(Conflict):
            self.store.save_gold(self.mid, self.gold_body())
        second = self.store.save_gold(self.mid, self.gold_body(base_revision=first["events"][0]["revision"], evidence="Revised"))
        self.assertEqual(second["events"][0]["gold"]["evidence"], "Revised")
        reloaded = AtlasStore(Store(self.root)).detail(self.mid)
        self.assertEqual(reloaded["events"][0]["gold"], second["events"][0]["gold"])
        with self.assertRaises(Conflict):
            self.store.save_map(self.mid, self.map_body)

    def test_export_allowlist_only_and_outside_map_excluded(self):
        self.store.save_gold(self.mid, self.gold_body())
        self.store.save_gold(self.mid, self.gold_body(event_id="0-1", status="outside_map", geometry=None))
        with zipfile.ZipFile(io.BytesIO(self.store.export(self.mid, "input"))) as archive:
            self.assertEqual(set(archive.namelist()), {"map.png", "tasks.jsonl", "prompt.txt", "manifest.json"})
            rows = [json.loads(s) for s in archive.read("tasks.jsonl").decode().splitlines()]
            self.assertEqual(len(rows), 1)
            self.assertEqual(set(rows[0]), {"event_id", "map_version", "image", "width", "height", "text", "question"})
            self.assertNotIn("SECRET", archive.read("tasks.jsonl").decode())
            self.assertEqual(hashlib.sha256(archive.read("map.png")).hexdigest(), self.current["active"]["image_sha256"])

    def test_export_rejects_unreviewed_and_corrupted_asset(self):
        with self.assertRaises(ValueError):
            self.store.export(self.mid, "input")
        self.store.save_gold(self.mid, self.gold_body())
        self.store.asset_path(self.current["active"]["version"]).write_bytes(b"corrupt")
        with self.assertRaises(ValueError):
            self.store.export(self.mid, "input")

    def test_bad_crops_and_rotations(self):
        for change in ({"crop": [-1, 0, 100, 100]}, {"crop": [0, 0, 501, 200]}, {"crop": [0, 0, 1, 1]},
                       {"crop": [0.0, 0, 100, 100]}, {"rotation": 45}, {"max_side": 9000}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.store.save_map(self.mid, {**self.map_body, "base_revision": self.current["revision"], **change})

    def test_rotation_output_dimensions(self):
        result = self.store.save_map(self.mid, {**self.map_body, "base_revision": self.current["revision"], "rotation": 90})
        self.assertEqual((result["active"]["width"], result["active"]["height"]), (250, 300))

    def test_invalid_gold(self):
        for change in ({"evidence": ""}, {"geometry": None}, {"status": "outside_map"},
                       {"geometry": {"type": "point", "coordinates": [[300, 0]]}},
                       {"geometry": {"type": "point", "coordinates": [[float('nan'), 0]]}},
                       {"geometry": {"type": "polygon", "coordinates": [[0, 0], [30, 30], [0, 30], [30, 0]]}}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.store.save_gold(self.mid, self.gold_body(**change))

    def test_predictions_separate_and_reject_wrong_version(self):
        body = {"map_version": self.current["active"]["version"], "model": "test-only", "predictions": [
            {"event_id": "0-0", "geometry": {"type": "line", "coordinates": [[0, 0], [80, 80]]}}]}
        result = self.store.prediction(self.mid, body)
        self.assertIsNone(result["events"][0]["gold"])
        self.assertEqual(result["events"][0]["prediction"]["model"], "test-only")
        with self.assertRaises(Conflict):
            self.store.prediction(self.mid, {**body, "map_version": "wrong"})
        with self.assertRaises(ValueError):
            self.store.prediction(self.mid, {**body, "predictions": body["predictions"]*2})

    def test_unknown_assets_and_events(self):
        with self.assertRaises(KeyError):
            self.store.asset_path("../../.env")
        with self.assertRaises(KeyError):
            self.store.save_gold(self.mid, self.gold_body(event_id="unknown"))

    def test_predictions_keep_latest_per_model_and_event(self):
        body = {"map_version": self.current["active"]["version"], "model": "gpt-5", "predictions": [
            {"event_id": "0-0", "geometry": {"type": "point", "coordinates": [[40, 50]]}}]}
        self.store.prediction(self.mid, body)
        self.store.prediction(self.mid, {**body, "model": "Qwen/Qwen3-VL-8B-Instruct", "predictions": [
            {"event_id": "0-0", "geometry": {"type": "point", "coordinates": [[80, 90]]}}]})
        result = self.store.prediction(self.mid, {**body, "predictions": [{"event_id": "0-0", "geometry": None}]})
        both = result["events"][0]["predictions"]
        self.assertEqual(len(both), 2)
        self.assertIsNone(both["gpt-5"]["geometry"])
        self.assertEqual(both["Qwen/Qwen3-VL-8B-Instruct"]["geometry"]["coordinates"], [[80, 90]])
        self.assertEqual(result["events"][1]["predictions"], {})
        colors = {m["id"]: m["color"] for m in result["prediction_models"]}
        self.assertNotEqual(colors["gpt-5"], colors["Qwen/Qwen3-VL-8B-Instruct"])
        changed = self.store.save_map(self.mid, {**self.map_body, "base_revision": result["revision"],
                                                "crop": [80, 100, 400, 350]})
        self.assertEqual(changed["prediction_models"], [])
        self.assertEqual(changed["events"][0]["predictions"], {})

    def test_prediction_overlay_selects_model_without_changing_clean_map(self):
        body = {"map_version": self.current["active"]["version"], "model": "gpt-5", "predictions": [
            {"event_id": "0-0", "geometry": {"type": "point", "coordinates": [[40, 100]]}}]}
        self.store.prediction(self.mid, body)
        qwen = "Qwen/Qwen3-VL-8B-Instruct"
        self.store.prediction(self.mid, {**body, "model": qwen, "predictions": [
            {"event_id": "0-0", "geometry": {"type": "point", "coordinates": [[80, 150]]}}]})
        path = self.store.asset_path(self.current["active"]["version"])
        before = path.read_bytes()
        for model, point, color in [("gpt-5", (40, 100), (40, 123, 224)), (qwen, (80, 150), (22, 128, 93))]:
            with Image.open(io.BytesIO(self.store.overlay(self.mid, "0-0", "predictions", model))) as im:
                self.assertEqual(im.getpixel(point), color)
                self.assertEqual(im.info["model"], model)
        self.assertEqual(before, path.read_bytes())
        with self.assertRaises(ValueError):
            self.store.overlay(self.mid, "0-0", "predictions", "nonexistent-model")

    def test_runner_reads_only_clean_package_and_parses_geometry(self):
        self.store.save_gold(self.mid, self.gold_body())
        path = self.root / "input.zip"
        path.write_bytes(self.store.export(self.mid, "input"))
        manifest, png, tasks, prompt = read_package(path)
        self.assertEqual(manifest["map_version"], self.current["active"]["version"])
        self.assertEqual(parse_geometry('{"event_id":"0-0","geometry":null}', tasks[0])["geometry"], None)
        with self.assertRaises(ValueError):
            parse_geometry('{"event_id":"wrong","geometry":null}', tasks[0])
        client = Mock()
        client.responses.create.return_value = SimpleNamespace(output_text='{"event_id":"0-0","geometry":null}', usage=None)
        raw, _ = call_model(client, "responses", "test", png, tasks[0], prompt, 256)
        self.assertEqual(parse_geometry(raw, tasks[0])["event_id"], "0-0")
        args = client.responses.create.call_args.kwargs
        self.assertFalse(args["store"])
        self.assertNotIn("SECRET", json.dumps(args))
        self.assertTrue(args["input"][0]["content"][1]["image_url"].startswith("data:image/png;base64,"))

    def test_runner_rejects_extra_files(self):
        path = self.root / "bad.zip"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("gold.json", "{}")
        with self.assertRaises(ValueError):
            read_package(path)

    def test_local_runner_does_not_load_credentials_or_call_api(self):
        self.store.save_gold(self.mid, self.gold_body())
        path = self.root / "input.zip"
        path.write_bytes(self.store.export(self.mid, "input"))
        output = self.root / "local.json"
        argv = ["run", "--input", str(path), "--output", str(output),
                "--backend", "qwen-local", "--model", "cached-test", "--execute"]
        with patch("sys.argv", argv), patch.object(run_atlas_vlm, "load_env_file") as env, \
                patch.object(run_atlas_vlm, "call_model") as remote, \
                patch.object(run_atlas_vlm, "load_local_qwen", return_value=(None, None, {"device": "test"})), \
                patch.object(run_atlas_vlm, "call_local_qwen", return_value=(
                    '{"event_id":"0-0","geometry":{"type":"point","coordinates":[[20,30]]}}',
                    {"input_tokens": 10, "output_tokens": 5})) as local:
            run_atlas_vlm.main()
            env.assert_not_called()
            remote.assert_not_called()
            self.assertEqual(local.call_count, 1)
            self.assertNotIn("SECRET", local.call_args.args[2]["text"])
        self.assertEqual(json.loads(output.read_text())["predictions"][0]["event_id"], "0-0")
        audit = json.loads(output.with_suffix(".attempts.jsonl").read_text())
        self.assertIsNone(audit["base_url"])
        self.assertEqual(audit["local_config"]["device"], "test")

    def test_local_dry_run_does_not_load_model(self):
        self.store.save_gold(self.mid, self.gold_body())
        path = self.root / "input.zip"
        path.write_bytes(self.store.export(self.mid, "input"))
        with patch("sys.argv", ["run", "--input", str(path), "--backend", "qwen-local"]), \
                patch.object(run_atlas_vlm, "load_local_qwen") as load:
            run_atlas_vlm.main()
            load.assert_not_called()

    def test_http_csrf_exports_and_image_routes(self):
        server = make_server(0, self.root)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        base = f"http://127.0.0.1:{server.server_address[1]}"
        with urlopen(base + "/api/atlas") as response:
            csrf = json.load(response)["csrf"]
        body = json.dumps(self.gold_body()).encode()
        with self.assertRaises(HTTPError) as ctx:
            urlopen(Request(base + f"/api/atlas/{self.mid}/gold", data=body))
        self.assertEqual(ctx.exception.code, 403)
        server.token = "new-session-after-restart"
        with self.assertRaises(HTTPError) as ctx:
            urlopen(Request(base + f"/api/atlas/{self.mid}/gold", data=body,
                            headers={"X-CSRF-Token": csrf}))
        self.assertEqual(ctx.exception.code, 403)
        self.assertIsNone(self.store.detail(self.mid)["events"][0]["gold"])
        with urlopen(base + "/api/atlas") as response:
            csrf = json.load(response)["csrf"]
        req = Request(base + f"/api/atlas/{self.mid}/gold", data=body, headers={"X-CSRF-Token": csrf})
        with urlopen(req) as response:
            self.assertEqual(response.status, 200)
        with self.assertRaises(HTTPError) as ctx:
            urlopen(req)
        self.assertEqual(ctx.exception.code, 409)
        with urlopen(base + f"/atlas-assets/{self.current['active']['version']}") as response:
            self.assertEqual(response.headers["Content-Type"], "image/png")
        with urlopen(base + f"/api/atlas/{self.mid}/input") as response:
            self.assertEqual(response.headers["Content-Type"], "application/zip")
        with self.assertRaises(HTTPError) as ctx:
            urlopen(base + f"/api/atlas/{self.mid}/input?version=stale")
        self.assertEqual(ctx.exception.code, 409)


if __name__ == "__main__":
    unittest.main()
