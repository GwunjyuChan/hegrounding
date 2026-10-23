import io
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

from PIL import Image
from annotation_server import make_server
from atlas_store import Conflict, append


class PlaceLabTests(unittest.TestCase):
    def test_independent_map_upload_persistence_and_catalog(self):
        from atlas_store import AtlasStore
        from place_lab import PlaceLab
        result = self.lab.create_map({'source_id': self.source['id'], 'title': 'Uploaded experiment'})
        self.assertEqual(result['events'], [])
        self.assertIsNone(result['reference_event'])
        self.assertEqual(result['active']['base_map_role'], 'uploaded_map')
        self.assertEqual(self.lab.create_map({'source_id': self.source['id'], 'title': 'Retry'})['id'], result['id'])
        fresh = PlaceLab(AtlasStore(self.server.store), self.server.store.lock)
        ids = {m['id'] for m in fresh.catalog()['maps']}
        self.assertIn(result['id'], ids)
        self.assertIn(self.mid, ids)  # Previously annotated place maps remain available.
        self.assertEqual(fresh.detail(result['id'])['tasks'], [])
        task = fresh.add(result['id'], {'map_version': result['active']['version'], 'place_name': 'New label'})
        self.assertEqual(len(task['tasks']), 1)

    def test_place_input_package_and_prediction_import(self):
        from run_atlas_vlm import read_package
        self.lab.save_gold(self.mid, self.body())
        package = self.root / 'input.zip'
        package.write_bytes(self.lab.export_input(self.mid))
        manifest, _, tasks, prompt = read_package(package)
        self.assertEqual(tasks[0]['event_id'], self.task_id)
        self.assertNotIn('SECRET', json.dumps(tasks))
        self.assertNotIn('PRIVATE', json.dumps(tasks))
        self.assertIn('printed place-name', prompt)
        row = {'event_id': self.task_id, 'geometry': {'type': 'point', 'coordinates': [[200, 150]]}}
        body = {'map_version': manifest['map_version'], 'model': 'test-model', 'predictions': [row]}
        detail = self.lab.import_predictions(self.mid, body)
        self.assertTrue(detail['tasks'][0]['predictions'][0]['comparison']['hit'])
        self.assertEqual(detail['tasks'][0]['predictions'][0]['model'], 'test-model')
        before = (self.lab.base / 'predictions.jsonl').read_bytes()
        for bad in ({**body, 'map_version': 'old'}, {**body, 'predictions': [row, row]},
                    {**body, 'predictions': [{**row, 'event_id': 'unknown'}]},
                    {**body, 'predictions': [{**row, 'status': 'error'}]}):
            with self.assertRaises(ValueError):
                self.lab.import_predictions(self.mid, bad)
        self.assertEqual(before, (self.lab.base / 'predictions.jsonl').read_bytes())
        failed = self.lab.import_predictions(self.mid, {**body, 'predictions': [],
            'errors': [{'event_id': self.task_id, 'error_type': 'ValueError'}]})
        self.assertEqual(failed['tasks'][0]['predictions'][0]['status'], 'error')

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / "benchmark").mkdir()
        (self.root / "maps").mkdir()
        Image.new("RGB", (400, 300), "white").save(self.root / "maps/ref.png")
        (self.root / "benchmark/zurich_pilot_10.jsonl").write_text(json.dumps({
            "event_id": "Z1", "battle_id": "zurich_second_1799", "image": "maps/ref.png",
            "event_text": "PRIVATE EVENT", "target_question": "PRIVATE QUESTION"}) + "\n")
        self.server = make_server(0, self.root)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.place_jobs.close)
        self.atlas = self.server.atlas
        self.lab = self.server.place_lab
        self.mid = next(iter(self.atlas.groups))
        buf = io.BytesIO()
        Image.new("RGB", (400, 300), "#e1eadf").save(buf, format="PNG")
        self.source = self.atlas.import_source(buf.getvalue(), "base.png")
        self.map_body = {"base_revision": None, "source_id": self.source["id"], "crop": [0, 0, 400, 300],
                         "rotation": 0, "max_side": 3200, "title": "test", "provenance": "test"}
        self.map = self.atlas.save_map(self.mid, self.map_body)["active"]
        self.add_body = {"map_version": self.map["version"], "place_name": "Zurich"}
        self.task_id = self.lab.add(self.mid, self.add_body)["task_id"]

    def body(self, **changes):
        return {"task_id": self.task_id, "map_version": self.map["version"], "base_revision": None,
                "status": "accepted", "geometry": {"type": "point", "coordinates": [[200, 150]]},
                "tolerance_px": 10, "confidence": 5, "evidence": "SECRET GOLD", "annotator": "test", **changes}

    def test_task_dedup_gold_persistence_and_input_isolation(self):
        self.assertEqual(self.lab.add(self.mid, self.add_body)["task_id"], self.task_id)
        before = self.atlas.asset_path(self.map["version"]).read_bytes()
        detail = self.lab.save_gold(self.mid, self.body())
        self.assertEqual(detail["tasks"][0]["gold"]["confidence"], 5)
        self.assertFalse((self.atlas.base / "gold.jsonl").exists())
        self.assertEqual(before, self.atlas.asset_path(self.map["version"]).read_bytes())
        payload, image = self.lab.clean_input(self.mid, {**self.body(), "model": "evil", "place_name": "override"})
        self.assertEqual(image, before)
        text = json.dumps(payload)
        for private in ("SECRET", "PRIVATE", "override", "confidence", "geometry", "annotator"):
            self.assertNotIn(private, text)
        self.assertEqual(payload["model"], "Qwen/Qwen3-VL-8B-Instruct")
        self.assertEqual(set(payload["task"]), {"event_id", "width", "height", "text", "question"})

    def test_validation_revisions_and_version_isolation(self):
        for changes in ({"confidence": True}, {"confidence": 6}, {"geometry": None},
                        {"tolerance_px": -1}, {"geometry": {"type": "point", "coordinates": [[400, 3]]}}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.lab.save_gold(self.mid, self.body(**changes))
        first = self.lab.save_gold(self.mid, self.body())
        with self.assertRaises(Conflict):
            self.lab.save_gold(self.mid, self.body())
        self.lab.save_gold(self.mid, self.body(base_revision=first["tasks"][0]["revision"], confidence=3))
        old = self.atlas.detail(self.mid)
        new = self.atlas.save_map(self.mid, {**self.map_body, "base_revision": old["revision"], "crop": [20, 20, 380, 280]})
        self.assertEqual(self.lab.detail(self.mid)["tasks"], [])
        with self.assertRaises(Conflict):
            self.lab.clean_input(self.mid, self.body())
        self.atlas.restore(self.mid, {"base_revision": new["revision"], "version": self.map["version"]})
        self.assertEqual(self.lab.detail(self.mid)["tasks"][0]["gold"]["confidence"], 3)

    def test_predictions_and_polygon_comparison_stay_separate(self):
        self.lab.save_gold(self.mid, self.body(geometry={"type": "polygon", "coordinates": [[100, 100], [250, 100], [250, 200], [100, 200]]}))
        append(self.lab.base / "predictions.jsonl", {"job_id": "demo", "task_id": self.task_id,
            "map_id": self.mid, "map_version": self.map["version"], "geometry": {"type": "point", "coordinates": [[200, 150]]}})
        row = self.lab.detail(self.mid)["tasks"][0]
        self.assertTrue(row["predictions"][0]["comparison"]["hit"])
        self.assertEqual(self.atlas.detail(self.mid)["prediction_models"], [])

    def test_http_csrf_and_place_routes(self):
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.server.shutdown)
        url = f"http://127.0.0.1:{self.server.server_address[1]}"
        with urlopen(url + f"/api/atlas/{self.mid}/places") as r:
            self.assertEqual(len(json.load(r)["tasks"]), 1)
        data = json.dumps(self.body()).encode()
        with self.assertRaises(HTTPError) as exc:
            urlopen(Request(url + f"/api/atlas/{self.mid}/place-gold", data=data))
        self.assertEqual(exc.exception.code, 403)
        headers = {"Content-Type": "application/json", "X-CSRF-Token": self.server.token, "Origin": url}
        with urlopen(Request(url + '/api/atlas/upload?name=fixture.png',
                             data=(self.root / 'maps/ref.png').read_bytes(), headers=headers)) as r:
            source = json.load(r)
        create = json.dumps({'source_id': source['id'], 'title': 'Independent HTTP test'}).encode()
        with urlopen(Request(url + '/api/place-maps', data=create, headers=headers)) as r:
            created = json.load(r)
        self.assertEqual(created['kind'], 'place_lab')
        self.assertEqual(created['events'], [])
        with urlopen(url + '/api/place-maps') as r:
            self.assertIn(created['id'], {m['id'] for m in json.load(r)['maps']})
        with urlopen(Request(url + f"/api/atlas/{self.mid}/place-gold", data=data, headers=headers)) as r:
            self.assertEqual(json.load(r)["tasks"][0]["gold"]["confidence"], 5)
        with patch.object(self.server.place_jobs, "start", return_value={"status": "running"}) as start:
            with urlopen(Request(url + f"/api/atlas/{self.mid}/place-predict", data=data, headers=headers)) as r:
                self.assertEqual(r.status, 202)
            start.assert_called_once()

    def test_worker_launch_is_fixed_and_completion_persists_result(self):
        finished = threading.Event()
        class FakeProcess:
            def __init__(self, argv, **kwargs):
                self.argv = argv
                directory = Path(argv[-1])
                payload = json.loads((directory / "input.json").read_text())
                result = {"status": "valid", "elapsed_seconds": 0.1, "prediction": {
                    "event_id": payload["task"]["event_id"], "geometry": {"type": "point", "coordinates": [[20, 30]]}}}
                (directory / "result.json").write_text(json.dumps(result))
            def wait(self, **kwargs):
                return 0
        real_write = self.server.place_jobs.write_state
        def write(directory, state):
            real_write(directory, state)
            if state["status"] != "running":
                finished.set()
        with patch("place_lab.subprocess.Popen", side_effect=FakeProcess) as launch, patch.object(self.server.place_jobs, "write_state", side_effect=write):
            state = self.server.place_jobs.start(self.mid, self.body())
            self.assertTrue(finished.wait(5))
        self.assertEqual(self.server.place_jobs.state(self.mid, state["job_id"])["status"], "completed")
        self.assertTrue(launch.call_args.args[0][1].endswith("place_lab_worker.py"))
        self.assertEqual(len(self.lab.detail(self.mid)["tasks"][0]["predictions"]), 1)
        with self.assertRaises(KeyError):
            self.server.place_jobs.state(self.mid, "../bad")

    def test_batch_uses_saved_places_and_no_gold(self):
        with self.assertRaises(ValueError):
            self.lab.clean_batch(self.mid, self.body())
        self.lab.save_gold(self.mid, self.body())
        self.lab.add(self.mid, {**self.add_body, "place_name": "Unfinished"})
        payload, image = self.lab.clean_batch(self.mid, self.body())
        self.assertNotIn("task", payload)
        self.assertEqual([t["event_id"] for t in payload["tasks"]], [self.task_id])
        for private in ("SECRET", "PRIVATE", "confidence", "geometry", "annotator", "Unfinished"):
            self.assertNotIn(private, json.dumps(payload))
        self.assertEqual(image, self.atlas.asset_path(self.map["version"]).read_bytes())

    def test_batch_worker_loads_once_and_continues_after_bad_response(self):
        from place_lab_worker import main
        self.lab.save_gold(self.mid, self.body())
        payload, image = self.lab.clean_batch(self.mid, self.body())
        first = payload["tasks"][0]
        payload["tasks"] = [{**first, "event_id": f"L{i}"} for i in range(3)]
        directory = self.root / "batch"
        directory.mkdir()
        (directory / "input.json").write_text(json.dumps(payload))
        (directory / "map.png").write_bytes(image)
        raw = [json.dumps({"event_id": "L0", "geometry": {"type": "point", "coordinates": [[500, 500]]}}),
               "broken json", json.dumps({"event_id": "L2", "geometry": None})]
        with patch("place_lab_worker.load_local_qwen", return_value=(None, None, {})) as load, \
                patch("place_lab_worker.call_local_qwen", side_effect=[(r, {}) for r in raw]) as call:
            self.assertEqual(main(directory), 0)
        load.assert_called_once()
        self.assertEqual(call.call_count, 3)
        result = json.loads((directory / "result.json").read_text())
        self.assertEqual([r["status"] for r in result["results"]], ["valid", "error", "abstained"])
        self.assertEqual(result["results"][0]["prediction"]["geometry"]["coordinates"], [[200, 150]])
        self.assertEqual(json.loads((directory / "progress.json").read_text()), {"done": 3, "total": 3})
        self.assertEqual(len((directory / "responses.jsonl").read_text().splitlines()), 3)

    def test_batch_job_persists_failures_and_successes_together(self):
        self.lab.save_gold(self.mid, self.body())
        second = self.lab.add(self.mid, {**self.add_body, "place_name": "Second"})["task_id"]
        self.lab.save_gold(self.mid, self.body(task_id=second))
        finished = threading.Event()
        class FakeProcess:
            def __init__(self, argv, **kwargs):
                directory = Path(argv[-1])
                tasks = json.loads((directory / "input.json").read_text())["tasks"]
                results = [{"task_id": tasks[0]["event_id"], "status": "valid", "elapsed_seconds": 1,
                            "prediction": {"geometry": {"type": "point", "coordinates": [[20, 30]]}}},
                           {"task_id": tasks[1]["event_id"], "status": "error", "elapsed_seconds": 1, "error_type": "ValueError"}]
                (directory / "result.json").write_text(json.dumps({"status": "completed", "results": results, "elapsed_seconds": 3}))
            def wait(self, **kwargs):
                return 0
        real_write = self.server.place_jobs.write_state
        def write(directory, state):
            real_write(directory, state)
            if state["status"] != "running":
                finished.set()
        with patch("place_lab.subprocess.Popen", side_effect=FakeProcess), patch.object(self.server.place_jobs, "write_state", side_effect=write):
            from run_place_batch import main
            thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            thread.start()
            self.addCleanup(self.server.shutdown)
            with patch("run_place_batch.time.sleep"):
                self.assertEqual(main(["--port", str(self.server.server_address[1]), "--execute"]), 1)
            self.assertTrue(finished.wait(5))
            state = self.server.place_jobs.recent(self.mid)[0]
        final = self.server.place_jobs.state(self.mid, state["job_id"])
        self.assertEqual(final["counts"], {"valid": 1, "error": 1, "abstained": 0})
        self.assertEqual(len(final["results"]), 2)
        rows = self.lab.detail(self.mid)["tasks"]
        self.assertTrue(all(len(r["predictions"]) == 1 for r in rows))
        self.assertTrue(all(r["predictions"][0]["job_id"] == state["job_id"] for r in rows))


if __name__ == "__main__":
    unittest.main()
