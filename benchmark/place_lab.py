"""Versioned interactive label experiments and isolated local inference jobs."""
from __future__ import annotations

import fcntl
import io
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import uuid
import zipfile

from annotate_geo import load_jsonl
from atlas_store import append, digest, stamp, text_field, token, Conflict

MODEL = "Qwen/Qwen3-VL-8B-Instruct"


class PlaceLab:
    def __init__(self, atlas, lock):
        self.atlas, self.lock = atlas, lock
        self.base = atlas.base / "place_lab"

    def records(self, kind):
        return load_jsonl(self.base / f"{kind}.jsonl")

    def catalog(self):
        used = {r['map_id'] for r in self.records('tasks')}
        maps = [m for m in self.atlas.catalog()['maps'] if m.get('kind') == 'place_lab' or m['id'] in used]
        return {'maps': maps}

    def create_map(self, body):
        source = self.atlas.asset(body.get('source_id'))
        title = text_field(body, 'title', 200)
        # A content-derived ID makes retries of the same upload idempotent.
        mid = digest(('place_lab:' + source['id']).encode())[:16]
        if mid in self.atlas.groups and self.atlas.detail(mid)['active']:
            return self.atlas.detail(mid)
        if source['width'] < 32 or source['height'] < 32:
            raise ValueError('实验地图宽高不得小于 32 像素。')
        group = {'id': mid, 'kind': 'place_lab', 'title': title, 'battle_name': title,
                 'battle_id': '', 'reference_event': None, 'reference_image': None,
                 'events': [], 'created_at': stamp()}
        if mid not in self.atlas.groups:
            append(self.base / 'maps.jsonl', group)
            self.atlas.groups[mid] = group
        return self.atlas.save_map(mid, {'base_revision': None, 'source_id': source['id'],
            'crop': [0, 0, source['width'], source['height']], 'rotation': 0, 'max_side': 6000,
            'title': title, 'provenance': 'User-uploaded place-name experiment map: ' + source['name']})

    def export_input(self, mid):
        active = self.atlas.detail(mid)['active']
        if not active:
            raise ValueError('请先上传实验地图。')
        payload, png = self.clean_batch(mid, {'map_version': active['version'], 'coordinate_mode': 'pixels'})
        rows = [{**r, 'image': 'map.png', 'map_version': active['version']} for r in payload['tasks']]
        prompt = ('Locate the center of the target printed place-name label on the supplied map. '
                  'Return JSON with event_id and geometry: {type: point, coordinates: [[x,y]]}. '
                  'Use original image pixels, top-left origin, x rightward, y downward. '
                  'Return geometry: null when the label cannot be found. Do not use geographic coordinates.')
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('map.png', png)
            archive.writestr('tasks.jsonl', '\n'.join(json.dumps(r, ensure_ascii=False) for r in rows) + '\n')
            archive.writestr('prompt.txt', prompt)
            archive.writestr('manifest.json', json.dumps({'map_version': active['version'],
                'image_sha256': active['image_sha256'], 'coordinate_system': 'image_pixels_top_left', 'event_count': len(rows)}))
        return output.getvalue()

    def import_predictions(self, mid, body):
        active = self.active(mid, body.get('map_version'))
        model = text_field(body, 'model', 200)
        rows = body.get('predictions')
        errors = body.get('errors', [])
        if not isinstance(rows, list) or not isinstance(errors, list) or any(not isinstance(e, dict) for e in errors):
            raise ValueError('预测文件格式无效。')
        rows = rows + [{'event_id': e.get('event_id'), 'geometry': None, 'status': 'error',
                        'error_type': e.get('error_type')} for e in errors]
        ids = {r['id'] for r in self.tasks(mid, active['version'])}
        if not isinstance(rows, list) or not 1 <= len(rows) <= len(ids):
            raise ValueError('预测数量无效。')
        seen, records, job = set(), [], uuid.uuid4().hex
        for row in rows:
            if not isinstance(row, dict) or row.get('event_id') not in ids or row['event_id'] in seen:
                raise ValueError('未知或重复的地名 ID。')
            seen.add(row['event_id'])
            geom = row.get('geometry')
            status = row.get('status', 'valid' if geom else 'abstained')
            if status not in {'valid', 'abstained', 'error'} or (status == 'valid') != (geom is not None):
                raise ValueError('预测状态与几何不一致。')
            if geom is not None:
                geom = self.atlas.geometry(geom, active['width'], active['height'])
                if geom['type'] != 'point':
                    raise ValueError('地名预测须为单点。')
            records.append({'job_id': job, 'map_id': mid, 'map_version': active['version'],
                'task_id': row['event_id'], 'model': model, 'geometry': geom, 'batch': True,
                'coordinate_mode': 'pixels', 'status': status, 'elapsed_seconds': 0,
                'error_type': str(row.get('error_type') or '')[:200],
                'created_at': stamp(), 'imported': True})
        for row in records:
            append(self.base / 'predictions.jsonl', row)
        return self.detail(mid)

    def active(self, mid, version):
        active = self.atlas.detail(mid)["active"]
        if not active or active["version"] != version:
            raise Conflict("底图已改变，请重新打开地名实验。")
        return active

    def tasks(self, mid, version):
        return [r for r in self.records("tasks") if r["map_id"] == mid and r["map_version"] == version]

    def task(self, mid, body):
        self.active(mid, body.get("map_version"))
        return next((r for r in self.tasks(mid, body["map_version"]) if r["id"] == body.get("task_id")), None)

    def detail(self, mid):
        active = self.atlas.detail(mid)["active"]
        if not active:
            return {"map": None, "tasks": [], "model": MODEL}
        tasks = self.tasks(mid, active["version"])
        gold = {r["task_id"]: r for r in self.records("gold") if r["map_version"] == active["version"] and r["map_id"] == mid}
        predictions = self.records("predictions")
        rows = []
        for task in tasks:
            ann = gold.get(task["id"])
            runs = [r for r in predictions if r["task_id"] == task["id"] and r["map_id"] == mid and r["map_version"] == active["version"]]
            if ann and ann["status"] == "accepted" and ann.get("geometry"):
                from compare_grounding_methods import point_distance
                for run in runs:
                    if run.get("geometry"):
                        distance = point_distance(run["geometry"]["coordinates"][0], ann["geometry"])
                        run["comparison"] = {"distance_px": distance, "gold_type": ann["geometry"]["type"],
                            "hit": distance <= (ann["tolerance_px"] or 0)}
            rows.append({**task, "gold": ann, "revision": token(ann), "predictions": list(reversed(runs))})
        return {"map": active, "tasks": rows, "model": MODEL}

    def add(self, mid, body):
        active = self.active(mid, body.get("map_version"))
        name = text_field(body, "place_name", 160)
        existing = next((r for r in self.tasks(mid, active["version"]) if r["place_name"] == name), None)
        if existing:
            return {"task_id": existing["id"], **self.detail(mid)}
        task = {"id": "L" + uuid.uuid4().hex[:12], "map_id": mid, "map_version": active["version"],
                "image_sha256": active["image_sha256"], "place_name": name,
                "target_kind": "printed_label_center", "created_at": stamp()}
        append(self.base / "tasks.jsonl", task)
        return {"task_id": task["id"], **self.detail(mid)}

    def save_gold(self, mid, body):
        task = self.task(mid, body)
        if task is None:
            raise KeyError("Unknown place")
        current = next(r for r in self.detail(mid)["tasks"] if r["id"] == task["id"])
        if "base_revision" not in body or body["base_revision"] != current["revision"]:
            raise Conflict("人工标注已更新，请刷新后重试。")
        active = self.active(mid, body["map_version"])
        geom = body.get("geometry")
        status = body.get("status")
        if status not in {"accepted", "ambiguous", "unlocatable"}:
            raise ValueError("请选择审核状态。")
        if geom is not None:
            geom = self.atlas.geometry(geom, active["width"], active["height"])
            if geom["type"] not in {"point", "polygon"}:
                raise ValueError("地名标注仅支持点或区域。")
        if status == "accepted" and geom is None:
            raise ValueError("通过的地名必须有人工标注。")
        confidence = body.get("confidence")
        if confidence is not None and (type(confidence) is not int or not 1 <= confidence <= 5):
            raise ValueError("置信度须为 1–5 或未审核。")
        tolerance = body.get("tolerance_px", 0)
        if type(tolerance) not in (int, float) or not math.isfinite(tolerance) or not 0 <= tolerance <= max(active["width"], active["height"]):
            raise ValueError("像素容差无效。")
        append(self.base / "gold.jsonl", {"task_id": task["id"], "map_id": mid,
            "map_version": active["version"], "image_sha256": active["image_sha256"],
            "geometry": geom, "status": status, "confidence": confidence,
            "tolerance_px": tolerance if geom and geom["type"] == "point" else None,
            "evidence": text_field(body, "evidence", 4000, required=False),
            "annotator": text_field(body, "annotator", 100), "created_at": stamp()})
        return self.detail(mid)

    def clean_input(self, mid, body):
        task = self.task(mid, body)
        if task is None:
            raise KeyError("Unknown place")
        active = self.active(mid, body["map_version"])
        image = self.atlas.asset_path(active["version"]).read_bytes()
        if digest(image) != active["image_sha256"]:
            raise ValueError("底图校验失败。")
        mode = body.get("coordinate_mode", "normalized_1000")
        if mode not in {"pixels", "normalized_1000"}:
            raise ValueError("未知坐标约定。")
        # Construct an allowlisted payload; annotations and previous predictions never enter it.
        return {"map_id": mid, "map_version": active["version"], "image_sha256": active["image_sha256"],
                "coordinate_mode": mode, "model": MODEL, "max_tokens": 1024,
                "task": {"event_id": task["id"], "width": active["width"], "height": active["height"],
                         "text": f"Target printed place-name label: {task['place_name']}.",
                         "question": f'Where is the center of the printed label "{task["place_name"]}"?'}}, image

    def clean_batch(self, mid, body):
        detail = self.detail(mid)
        self.active(mid, body.get("map_version"))
        selected = [t for t in detail["tasks"] if t["gold"] is not None]
        if not selected:
            raise ValueError("当前底图没有已保存人工标注的地名。")
        payload, image = self.clean_input(mid, {**body, "task_id": selected[0]["id"]})
        template = payload.pop("task")
        payload["tasks"] = [{**template, "event_id": t["id"],
            "text": f"Target printed place-name label: {t['place_name']}.",
            "question": f'Where is the center of the printed label "{t["place_name"]}"?'} for t in selected]
        return payload, image


class PlaceJobs:
    def __init__(self, lab):
        self.lab = lab
        self.guard = threading.Lock()
        self.process = None
        self.closed = False
        self.session_id = uuid.uuid4().hex

    def recent(self, mid):
        paths = sorted((self.lab.base / "runs").glob("*/state.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        return [self.state(mid, p.parent.name) for p in paths
                if json.loads(p.read_text())["map_id"] == mid][:20]

    def state(self, mid, job):
        if len(job) != 32 or any(c not in "0123456789abcdef" for c in job):
            raise KeyError(job)
        path = self.lab.base / "runs" / job / "state.json"
        if not path.exists():
            raise KeyError(job)
        data = json.loads(path.read_text())
        if data["map_id"] != mid:
            raise KeyError(job)
        if data["status"] == "running" and data.get("session_id") != self.session_id:
            return {**data, "status": "interrupted", "error": "服务已重启；请检查运行记录后重新预测。"}
        progress = path.with_name("progress.json")
        if data["status"] == "running" and progress.exists():
            data["progress"] = json.loads(progress.read_text())
        return data

    @staticmethod
    def write_state(directory, data):
        path = directory / "state.tmp"
        path.write_text(json.dumps(data, ensure_ascii=False, allow_nan=False))
        path.replace(directory / "state.json")

    def start(self, mid, body):
        with self.guard:
            if self.closed:
                raise Conflict("服务正在关闭。")
            handle = open(Path(tempfile.gettempdir()) / f"hegrounding-place-model-{os.getuid()}.lock", "a")
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                handle.close()
                raise Conflict("已有本地地名预测正在运行，请稍后再试。") from None
            try:
                with self.lab.lock:
                    payload, image = (self.lab.clean_batch if body.get("batch") else self.lab.clean_input)(mid, body)
                job = uuid.uuid4().hex
                directory = self.lab.base / "runs" / job
                directory.mkdir(parents=True)
                (directory / "input.json").write_text(json.dumps(payload, ensure_ascii=False))
                (directory / "map.png").write_bytes(image)
                state = {"job_id": job, "map_id": mid, "map_version": payload["map_version"],
                         "task_id": payload.get("task", {}).get("event_id"),
                         "task_ids": [t["event_id"] for t in payload.get("tasks", [payload.get("task")])],
                         "batch": "tasks" in payload, "status": "running", "created_at": stamp(),
                         "session_id": self.session_id}
                self.write_state(directory, state)
                threading.Thread(target=self.execute, args=(directory, payload, state, handle), daemon=True).start()
                return state
            except Exception:
                handle.close()
                raise

    def execute(self, directory, payload, state, handle):
        try:
            with (directory / "worker.log").open("w") as log:
                with self.guard:
                    if self.closed:
                        raise RuntimeError("Server closed")
                    self.process = subprocess.Popen([sys.executable, str(Path(__file__).with_name("place_lab_worker.py")),
                                                     str(directory.resolve())], stdout=log, stderr=log,
                                                    pass_fds=(handle.fileno(),))
                    process = self.process
                try:
                    returncode = process.wait(timeout=600 * len(state["task_ids"]))
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                    raise RuntimeError("Prediction timeout") from None
            result = json.loads((directory / "result.json").read_text())
            if returncode or result.get("status") == "error":
                raise ValueError(result.get("error_type", "WorkerError"))
            tasks = payload.get("tasks", [payload.get("task")])
            results = result.get("results", [result])
            if len(results) != len(tasks):
                raise ValueError("Incomplete batch result")
            records = []
            for task, item in zip(tasks, results):
                pred = item.get("prediction", {})
                if item.get("task_id", task["event_id"]) != task["event_id"]:
                    raise ValueError("Mismatched task result")
                geom = pred.get("geometry")
                if geom is not None:
                    self.lab.atlas.geometry(geom, task["width"], task["height"])
                records.append({"job_id": state["job_id"], "map_id": state["map_id"], "map_version": state["map_version"],
                      "task_id": task["event_id"], "model": MODEL, "geometry": geom, "batch": state["batch"],
                      "coordinate_mode": payload["coordinate_mode"], "status": item["status"],
                      "error_type": item.get("error_type"),
                      "elapsed_seconds": item["elapsed_seconds"], "usage": item.get("usage"),
                      "format_normalization": pred.get("format_normalization"), "created_at": stamp()})
            with self.lab.lock:
                for record in records:
                    append(self.lab.base / "predictions.jsonl", record)
            counts = {s: sum(r["status"] == s for r in records) for s in ("valid", "abstained", "error")}
            self.write_state(directory, {**state, "status": "completed", "counts": counts,
                                         "results": records, "elapsed_seconds": result["elapsed_seconds"]})
        except Exception as exc:
            self.write_state(directory, {**state, "status": "failed", "error_type": type(exc).__name__,
                "error": "本地预测失败或超时；输入和日志已保留，可重新运行。"})
        finally:
            with self.guard:
                self.process = None
            handle.close()

    def close(self):
        with self.guard:
            self.closed = True
            if self.process is not None and self.process.poll() is None:
                self.process.terminate()
