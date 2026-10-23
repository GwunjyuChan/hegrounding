#!/usr/bin/env python3
"""Loopback annotation app; public mode requires an authenticated HTTPS proxy."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import mimetypes
import os
import re
from pathlib import Path
import secrets
import threading
from urllib.parse import unquote, urlsplit, parse_qs

os.environ.setdefault("MPLBACKEND", "Agg")
from annotate_geo import FEATURE_TYPES, ROOT, load_jsonl, validate_geometry
from PIL import Image
from atlas_store import AtlasStore, Conflict
from place_lab import PlaceLab, PlaceJobs

STATIC = Path(__file__).with_name("gui")
BATTLES = (
    {"id": "san_sebastian_1813", "name": "圣塞巴斯蒂安围城", "label": "San Sebastián", "date": "1813.07–09", "country": "西班牙", "lat": 43.324, "lng": -1.981, "color": "#985575"},
    {"id": "bussaco_1810", "name": "布萨科战役 · 内伊进攻", "label": "Bussaco", "date": "1810.09.27", "country": "葡萄牙", "lat": 40.376, "lng": -8.365, "color": "#b45937"},
    {"id": "marengo_1800", "name": "Marengo 战后部署", "label": "Marengo", "date": "1800.06.15 · 依原图标题", "country": "意大利", "lat": 44.885, "lng": 8.679, "color": "#426ba5"},
    {"id": "zurich_second_1799", "name": "第二次苏黎世战役", "label": "Zürich", "date": "1799.09.25–26", "country": "瑞士", "lat": 47.377, "lng": 8.542, "color": "#177d70"},
    {"id": "borkowo", "name": "Borkowo 战斗", "label": "Borkowo", "date": "1806.12.24", "country": "波兰", "lat": 52.56, "lng": 20.67, "color": "#b45937"},
    {"id": "sochocin", "name": "Sochocin 战斗", "label": "Sochocin", "date": "1806.12.24", "country": "波兰", "lat": 52.69, "lng": 20.47, "color": "#b45937"},
    {"id": "wavre", "name": "瓦夫尔战役", "label": "Wavre", "date": "1815.06.18–19", "country": "比利时", "lat": 50.717, "lng": 4.61, "color": "#426ba5"},
)
BATTLES += tuple(json.loads(Path(__file__).with_name("map_expansion_battles.json").read_text(encoding="utf-8")))
DATASETS = (("benchmark/map_first_candidates.jsonl", "benchmark/map_first_annotations.jsonl"),
            ("benchmark/zurich_pilot_10.jsonl", "benchmark/zurich_annotations.jsonl"))


def revision(record):
    if record is None:
        return None
    return hashlib.sha256(json.dumps(record, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


class Store:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.lock = threading.Lock()
        self.records = {}
        self.outputs = {}
        self.images = {}
        self.dimensions = {}
        for source, destination in DATASETS:
            for rec in load_jsonl(self.root / source):
                eid = rec["event_id"]
                if eid in self.records:
                    raise ValueError(f"Duplicate event ID: {eid}")
                if rec["battle_id"] not in {b["id"] for b in BATTLES}:
                    raise ValueError(f"Unknown battle: {rec['battle_id']}")
                path = (self.root / rec["image"]).resolve()
                if not path.is_relative_to(self.root.resolve()):
                    raise ValueError("Map outside project")
                with Image.open(path) as image:
                    self.dimensions[eid] = image.size
                self.records[eid] = rec
                self.images[eid] = path
                self.outputs[eid] = self.root / destination

    def history(self, eid):
        return [r for r in load_jsonl(self.outputs[eid]) if r["event_id"] == eid]

    def event(self, eid):
        if eid not in self.records:
            raise KeyError(eid)
        history = self.history(eid)
        latest = history[-1] if history else None
        return {"record": self.records[eid], "annotation": latest, "revision": revision(latest),
                "history": list(reversed(history)), "dimensions": self.dimensions[eid]}

    def catalog(self):
        latest = {}
        for path in set(self.outputs.values()):
            latest.update({r["event_id"]: r for r in load_jsonl(path)})
        battles = []
        for battle in BATTLES:
            events = []
            for eid, rec in self.records.items():
                if rec["battle_id"] == battle["id"]:
                    events.append({"id": eid, "question": rec.get("target_question", ""),
                                   "status": latest.get(eid, {}).get("status", "pending")})
            battles.append({**battle, "events": events, "total": len(events),
                            "reviewed": sum(e["status"] != "pending" for e in events),
                            "accepted": sum(e["status"] == "accepted" for e in events)})
        return {"battles": battles, "feature_types": [code for code, _ in FEATURE_TYPES]}

    def save(self, eid, body):
        with self.lock:
            current = self.event(eid)
            if "base_revision" not in body or body["base_revision"] != current["revision"]:
                raise Conflict("此事件已在其他窗口更新，请重新打开后再保存。")
            status = body.get("status")
            if status not in {"accepted", "ambiguous", "unlocatable", "rejected"}:
                raise ValueError("请选择有效审核状态。")
            evidence = body.get("evidence")
            if not isinstance(evidence, str) or not evidence.strip() or len(evidence) > 20000:
                raise ValueError("请填写证据，且不超过 20000 字符。")
            annotator = body.get("annotator")
            if not isinstance(annotator, str) or not annotator.strip() or len(annotator) > 100:
                raise ValueError("请填写标注者姓名。")
            feature = body.get("geo_feature_type")
            if feature not in {code for code, _ in FEATURE_TYPES}:
                raise ValueError("请选择统一词表中的要素类型。")
            geometry = body.get("geometry")
            width, height = self.dimensions[eid]
            if geometry is not None:
                if not isinstance(geometry, dict) or geometry.get("type") not in {"point", "line", "polygon"}:
                    raise ValueError("无效的几何类型。")
                points = geometry.get("coordinates")
                if not isinstance(points, list) or not 1 <= len(points) <= 2000:
                    raise ValueError("顶点数量无效。")
                for point in points:
                    if not isinstance(point, list) or len(point) != 2 or any(
                        isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
                        for v in point
                    ):
                        raise ValueError("顶点必须为有限数值的像素坐标。")
                validate_geometry(geometry["type"], points, width, height)
                geometry = {"type": geometry["type"], "coordinates": points}
            elif status == "accepted":
                raise ValueError("通过的事件必须有地图标注。")
            tolerance = None
            if geometry and geometry["type"] in {"point", "line"}:
                tolerance = body.get("tolerance_px", 0)
                if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)) or not math.isfinite(tolerance) or not 0 <= tolerance <= max(width, height):
                    raise ValueError("容差必须是原图范围内的非负像素数。")
            ann = {**self.records[eid], "schema_version": 2, "status": status,
                   "evidence": evidence.strip(), "annotator": annotator.strip(),
                   "geometry": geometry, "geo_gold_px": geometry["coordinates"][0] if geometry and geometry["type"] == "point" else None,
                   "geo_feature_type": feature, "geo_feature_vocab_version": 1,
                   "tolerance_px": tolerance, "img_w": width, "img_h": height,
                   "coordinate_system": "image_pixels_top_left",
                   "gold_status": "human_annotated" if status == "accepted" else "not_accepted",
                   "updated_at": datetime.now(timezone.utc).isoformat()}
            path = self.outputs[eid]
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(ann, ensure_ascii=False, allow_nan=False) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            return self.event(eid)


class Handler(BaseHTTPRequestHandler):
    def send(self, status, data, mime="application/json; charset=utf-8"):
        if not isinstance(data, bytes):
            data = json.dumps(data, ensure_ascii=False, allow_nan=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(data)

    def trusted_host(self):
        if self.server.public_origin:
            return self.headers.get("Host") == urlsplit(self.server.public_origin).netloc
        port = self.server.server_address[1]
        return self.headers.get("Host") in {f"127.0.0.1:{port}", f"localhost:{port}"}

    def do_GET(self):
        if not self.trusted_host():
            return self.send(403, {"error": "Local host only"})
        path = unquote(urlsplit(self.path).path)
        try:
            if path == "/api/catalog":
                with self.server.store.lock:
                    catalog = self.server.store.catalog()
                return self.send(200, {**catalog, "csrf": self.server.token, "workspace": self.server.workspace})
            if path == "/api/atlas":
                with self.server.store.lock:
                    data = self.server.atlas.catalog()
                return self.send(200, {**data, "csrf": self.server.token, "workspace": self.server.workspace})
            if path == '/api/place-maps':
                with self.server.store.lock:
                    data = self.server.place_lab.catalog()
                return self.send(200, {**data, 'csrf': self.server.token, 'workspace': self.server.workspace,
                                       'model_jobs_enabled': not self.server.disable_model_jobs})
            if path.startswith("/api/atlas/"):
                parts = path.removeprefix("/api/atlas/").split("/")
                if len(parts) == 3 and parts[1] == "place-jobs":
                    return self.send(200, self.server.place_jobs.state(parts[0], parts[2]))
                with self.server.store.lock:
                    expected = parse_qs(urlsplit(self.path).query).get("version", [None])[0]
                    if expected is not None and (self.server.atlas.detail(parts[0])["active"] or {}).get("version") != expected:
                        raise Conflict("底图已更新，请刷新后再导出。")
                    if len(parts) == 1:
                        return self.send(200, self.server.atlas.detail(parts[0]))
                    if len(parts) == 2 and parts[1] == "places":
                        return self.send(200, {**self.server.place_lab.detail(parts[0]),
                                               "jobs": self.server.place_jobs.recent(parts[0])})
                    if len(parts) == 2 and parts[1] == 'place-input':
                        return self.send(200, self.server.place_lab.export_input(parts[0]), 'application/zip')
                    if len(parts) == 2 and parts[1] in {"input", "gold"}:
                        data = self.server.atlas.export(parts[0], parts[1])
                        return self.send(200, data, "application/zip" if parts[1] == "input" else "application/json")
                    if len(parts) == 4 and parts[1] == "overlay":
                        model = parse_qs(urlsplit(self.path).query).get("model", [None])[0]
                        return self.send(200, self.server.atlas.overlay(parts[0], parts[2], parts[3], model), "image/png")
                raise KeyError(path)
            if path.startswith("/api/event/"):
                with self.server.store.lock:
                    event = self.server.store.event(path.removeprefix("/api/event/"))
                return self.send(200, event)
            if path.startswith("/atlas-assets/"):
                file = self.server.atlas.asset_path(path.removeprefix("/atlas-assets/"))
            elif path.startswith("/maps/"):
                file = self.server.store.images[path.removeprefix("/maps/")]
            else:
                default = 'place-lab.html' if self.server.workspace['kind'] == 'isolated' else 'index.html'
                file = (STATIC / (default if path == "/" else path.lstrip("/"))).resolve()
                if not file.is_relative_to(STATIC.resolve()):
                    raise KeyError(path)
            if not file.is_file():
                raise KeyError(path)
            data = file.read_bytes()
            if file.suffix == ".html":
                data = data.replace(b'<base href="/">', f'<base href="{self.server.url_prefix}/">'.encode())
            return self.send(200, data, mimetypes.guess_type(file.name)[0] or "application/octet-stream")
        except KeyError:
            self.send(404, {"error": "Not found"})
        except Conflict as exc:
            self.send(409, {"error": str(exc)})
        except ValueError as exc:
            self.send(400, {"error": str(exc)})
        except OSError:
            self.send(500, {"error": "读取本地数据失败，请查看终端。"})

    def do_POST(self):
        if not self.trusted_host() or not secrets.compare_digest(self.headers.get("X-CSRF-Token", ""), self.server.token):
            return self.send(403, {"error": "Unauthorized local request"})
        origins = {self.server.public_origin} if self.server.public_origin else {None, "http://" + self.headers.get("Host", "")}
        if self.headers.get("Origin") not in origins:
            return self.send(403, {"error": "Cross-origin request rejected"})
        path = urlsplit(self.path).path
        if path != '/api/place-maps' and not path.startswith(("/api/event/", "/api/atlas/")):
            return self.send(404, {"error": "Not found"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if path == "/api/atlas/upload":
                if not 0 < length <= 512 * 1024 * 1024:
                    raise ValueError("文件须非空且不超过 512 MiB。")
                query = parse_qs(urlsplit(self.path).query)
                data = self.rfile.read(length)
                with self.server.store.lock:
                    source = self.server.atlas.import_source(data, query.get("name", ["upload"])[0],
                        int(query.get("page", ["1"])[0]))
                return self.send(200, source)
            if not 0 < length <= 200000:
                raise ValueError("请求过大或为空。")
            body = json.loads(self.rfile.read(length))
            if not isinstance(body, dict):
                raise ValueError("Invalid JSON object")
            if path == '/api/place-maps':
                with self.server.store.lock:
                    result = self.server.place_lab.create_map(body)
                return self.send(200, result)
            if path.startswith("/api/atlas/"):
                parts = unquote(path.removeprefix("/api/atlas/")).split("/")
                if len(parts) == 2 and parts[1] == "place-predict":
                    if self.server.disable_model_jobs:
                        return self.send(403, {"error": "Model inference is disabled on this server"})
                    return self.send(202, self.server.place_jobs.start(parts[0], body))
                actions = {"map": self.server.atlas.save_map, "use-reference": self.server.atlas.use_reference,
                           "reference-source": self.server.atlas.reference_source,
                           "gold": self.server.atlas.save_gold,
                           "restore": self.server.atlas.restore, "predictions": self.server.atlas.prediction,
                           "places": self.server.place_lab.add, "place-gold": self.server.place_lab.save_gold,
                           "place-predictions": self.server.place_lab.import_predictions}
                if len(parts) != 2 or parts[1] not in actions:
                    raise KeyError(path)
                with self.server.store.lock:
                    result = actions[parts[1]](parts[0], body)
                return self.send(200, result)
            self.send(200, self.server.store.save(unquote(path.removeprefix("/api/event/")), body))
        except Conflict as exc:
            self.send(409, {"error": str(exc)})
        except KeyError:
            self.send(404, {"error": "Unknown event"})
        except (ValueError, TypeError) as exc:
            self.send(400, {"error": str(exc)})
        except OSError:
            self.send(500, {"error": "保存失败，请检查磁盘和文件权限。"})


def workspace_info(store, event_port=8767, place_port=8769):
    for port in (event_port, place_port):
        if type(port) is not int or not 1 <= port <= 65535:
            raise ValueError("Workspace port must be in 1..65535")
    isolated = store.root.resolve() != ROOT.resolve()
    labels = bool(store.records) and all(r.get("place_name") for r in store.records.values())
    return {"kind": "isolated" if isolated else "main",
            "name": "地名实验工作区" if labels else "独立实验工作区" if isolated else "历史事件工作区",
            "item_label": "地名样本" if labels else "事件",
            "events_url": f"http://127.0.0.1:{event_port}/" if isolated else "/",
            "place_lab_url": "/place-lab.html" if isolated else f"http://127.0.0.1:{place_port}/place-lab.html"}


def make_server(port=8765, root=ROOT, event_port=8767, place_port=8769, *,
                public_origin=None, url_prefix="", events_url=None, place_lab_url=None,
                workspace_kind=None, disable_model_jobs=False):
    if public_origin:
        origin = urlsplit(public_origin)
        if (origin.scheme != "https" or not origin.hostname or origin.username or origin.password
                or origin.path or origin.query or origin.fragment
                or not re.fullmatch(r"https://[a-zA-Z0-9.-]+(?::[0-9]+)?", public_origin)):
            raise ValueError("Public origin must be an HTTPS origin without a path")
    if url_prefix and not re.fullmatch(r"(?:/[a-zA-Z0-9_-]+)+", url_prefix):
        raise ValueError("Invalid URL prefix")
    for url in (events_url, place_lab_url):
        if url is not None and not re.fullmatch(r"/(?:[a-zA-Z0-9_./-]*)", url):
            raise ValueError("Workspace links must be same-origin absolute paths")
        if url is not None and (url.startswith("//") or ".." in url):
            raise ValueError("Invalid workspace link")
    if workspace_kind not in {None, "main", "isolated"}:
        raise ValueError("Invalid workspace kind")
    store = Store(root)
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.public_origin = public_origin
    server.url_prefix = url_prefix
    server.disable_model_jobs = disable_model_jobs or bool(public_origin)
    server.store = store
    server.workspace = workspace_info(server.store, event_port, place_port)
    if workspace_kind:
        server.workspace["kind"] = workspace_kind
        if workspace_kind == "main":
            server.workspace.update(name="历史事件工作区", item_label="事件")
    if public_origin:
        server.workspace.update(events_url="/", place_lab_url=url_prefix + "/place-lab.html")
    if events_url is not None:
        server.workspace["events_url"] = events_url
    if place_lab_url is not None:
        server.workspace["place_lab_url"] = place_lab_url
    server.atlas = AtlasStore(server.store)
    server.place_lab = PlaceLab(server.atlas, server.store.lock)
    server.place_jobs = PlaceJobs(server.place_lab)
    server.token = secrets.token_hex(32)
    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--data-root", type=Path, default=ROOT, help="Alternate project root, e.g. an isolated test fixture")
    parser.add_argument("--event-workspace-port", type=int, default=8767, help="Main event workspace navigation port")
    parser.add_argument("--place-workspace-port", type=int, default=8769, help="Place experiment navigation port")
    parser.add_argument("--public-origin", help="HTTPS origin behind an authenticated reverse proxy; disables inference")
    parser.add_argument("--url-prefix", default="", help="Proxy-stripped mount path, e.g. /labels")
    parser.add_argument("--events-url", help="Same-origin event workspace URL")
    parser.add_argument("--place-lab-url", help="Same-origin place workspace URL")
    parser.add_argument("--workspace-kind", choices=("main", "isolated"))
    parser.add_argument("--disable-model-jobs", action="store_true")
    args = parser.parse_args()
    server = make_server(args.port, args.data_root, args.event_workspace_port, args.place_workspace_port,
                         public_origin=args.public_origin, url_prefix=args.url_prefix,
                         events_url=args.events_url, place_lab_url=args.place_lab_url,
                         workspace_kind=args.workspace_kind, disable_model_jobs=args.disable_model_jobs)
    print(f"Annotation GUI: http://127.0.0.1:{server.server_address[1]}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.place_jobs.close()
        server.server_close()


if __name__ == "__main__":
    main()
