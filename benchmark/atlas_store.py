"""Versioned clean map assets, separate gold labels and model-only exports."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

from PIL import Image, ImageDraw, ImageOps, PngImagePlugin
from annotate_geo import FEATURE_TYPES, load_jsonl, validate_geometry


class Conflict(ValueError):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


def stamp():
    return datetime.now(timezone.utc).isoformat()


def append(path, record):
    import os
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def token(record):
    return digest(json.dumps(record, sort_keys=True, ensure_ascii=False).encode()) if record else None


def prediction_style(model):
    name = model.rsplit("/", 1)[-1]
    if model.lower().startswith("gpt-5"):
        return {"id": model, "label": name.upper(), "color": "#287be0"}
    if "qwen" in model.lower():
        return {"id": model, "label": name, "color": "#16805d"}
    return {"id": model, "label": model, "color": "#9558aa"}


def text_field(body, key, limit=20000, required=True):
    value = body.get(key, "")
    if not isinstance(value, str) or len(value) > limit or (required and not value.strip()):
        raise ValueError(f"请填写有效的 {key}。")
    return value.strip()


class AtlasStore:
    def __init__(self, legacy):
        self.legacy = legacy
        self.root = legacy.root
        self.base = self.root / "benchmark/atlas"
        self.groups = {}
        for eid, record in legacy.records.items():
            key = digest(record["image"].encode())[:16]
            group = self.groups.setdefault(key, {"id": key, "reference_image": record["image"],
                "reference_event": eid, "battle_id": record["battle_id"], "events": []})
            group["events"].append(eid)

    def history(self, mid):
        if mid not in self.groups:
            raise KeyError(mid)
        return [r for r in load_jsonl(self.base / "maps.jsonl") if r["map_id"] == mid]

    def asset(self, sid):
        records = {r["id"]: r for r in load_jsonl(self.base / "sources.jsonl")}
        if sid not in records:
            raise KeyError(sid)
        return records[sid]

    def labels(self, mid, version, kind="gold"):
        latest = {}
        for r in load_jsonl(self.base / f"{kind}.jsonl"):
            if r["map_id"] == mid and r["map_version"] == version:
                latest[r["event_id"]] = r
        return latest

    def catalog(self):
        result = []
        for mid, group in self.groups.items():
            history = self.history(mid)
            active = history[-1] if history else None
            labels = self.labels(mid, active["version"]) if active else {}
            result.append({**group, "active": active, "revision": token(active),
                           "reviewed": len(labels), "total": len(group["events"])})
        return {"maps": result, "sources": load_jsonl(self.base / "sources.jsonl"),
                "feature_types": [k for k, _ in FEATURE_TYPES]}

    def model_predictions(self, mid, version):
        latest = {}
        for row in load_jsonl(self.base / "predictions.jsonl"):
            if row["map_id"] == mid and row["map_version"] == version:
                latest.setdefault(row["event_id"], {})[row["model"]] = row
        return latest

    def detail(self, mid):
        group = self.groups[mid]
        history = self.history(mid)
        active = history[-1] if history else None
        gold = self.labels(mid, active["version"]) if active else {}
        predictions = self.labels(mid, active["version"], "predictions") if active else {}
        by_model = self.model_predictions(mid, active["version"]) if active else {}
        models = sorted({model for event in by_model.values() for model in event})
        events = []
        for eid in group["events"]:
            rec = self.legacy.records[eid]
            ann = gold.get(eid)
            events.append({"id": eid, "question": rec.get("target_question", ""),
                "text": rec.get("event_text", ""), "source_text": rec.get("source_text", ""),
                "article_url": rec.get("article_url", ""), "caution": rec.get("annotation_caution", ""),
                "gold": ann, "revision": token(ann), "prediction": predictions.get(eid),
                "predictions": by_model.get(eid, {})})
        return {**group, "active": active, "revision": token(active), "events": events,
                "prediction_models": [prediction_style(model) for model in models],
                "history": list(reversed(history))}

    def import_source(self, data, name, page=1):
        if not 0 < len(data) <= 80 * 1024 * 1024:
            raise ValueError("文件必须小于 80 MB。")
        filename = Path(name).name[:180]
        pdf = data.startswith(b"%PDF-")
        source_hash = digest(data)
        if not isinstance(page, int) or isinstance(page, bool) or not 1 <= page <= 1000:
            raise ValueError("PDF 页码无效。")
        if pdf:
            if not shutil.which("pdftoppm"):
                raise ValueError("导入 PDF 需要 Poppler（pdftoppm）；也可导入 PNG/JPEG。")
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "source.pdf"
                path.write_bytes(data)
                try:
                    subprocess.run(["pdftoppm", "-f", str(page), "-l", str(page), "-singlefile",
                                    "-scale-to", "6000", "-png", str(path), str(Path(tmp) / "page")],
                                   check=True, capture_output=True, timeout=90)
                    with Image.open(Path(tmp) / "page.png") as im:
                        im.load()
                        image = im.convert("RGB")
                except (subprocess.SubprocessError, OSError) as exc:
                    raise ValueError("PDF 页面读取失败，请检查页码或改用图片。") from exc
        else:
            try:
                with Image.open(io.BytesIO(data)) as im:
                    if im.format not in {"PNG", "JPEG", "TIFF", "WEBP", "GIF"} or im.width * im.height > 60_000_000:
                        raise ValueError("不支持的图像格式或尺寸超过 6000 万像素。")
                    im.load()
                    image = ImageOps.exif_transpose(im).convert("RGB")
            except (OSError, Image.DecompressionBombError) as exc:
                raise ValueError("无法读取此图像。") from exc
        sid = digest(f"{source_hash}:{page if pdf else 0}:render6000-v1".encode())[:24]
        try:
            return self.asset(sid)
        except KeyError:
            pass
        self.base.mkdir(parents=True, exist_ok=True)
        originals = self.base / "originals"
        originals.mkdir(exist_ok=True)
        original = originals / (source_hash + (".pdf" if pdf else ".image"))
        if not original.exists():
            original.write_bytes(data)
        images = self.base / "assets"
        images.mkdir(exist_ok=True)
        image.save(images / f"{sid}.png")
        record = {"id": sid, "name": filename, "page": page if pdf else None,
                  "width": image.width, "height": image.height, "original_sha256": source_hash,
                  "pixel_sha256": digest(image.tobytes()), "render_max_side": 6000 if pdf else None,
                  "created_at": stamp()}
        append(self.base / "sources.jsonl", record)
        return record

    def save_map(self, mid, body):
        current = self.detail(mid)
        if "base_revision" not in body or body["base_revision"] != current["revision"]:
            raise Conflict("底图已更新，请刷新地图集。")
        source = self.asset(body.get("source_id"))
        crop = body.get("crop")
        if not isinstance(crop, list) or len(crop) != 4 or any(type(v) is not int for v in crop):
            raise ValueError("裁切框必须是四个整数 [left, top, right, bottom]。")
        x0, y0, x1, y1 = crop
        if not (0 <= x0 < x1 <= source["width"] and 0 <= y0 < y1 <= source["height"] and x1-x0 >= 32 and y1-y0 >= 32):
            raise ValueError("裁切框越界或宽高不足 32 像素。")
        angle = body.get("rotation", 0)
        if type(angle) is not int or angle not in (0, 90, 180, 270):
            raise ValueError("旋转角度须为 0、90、180、270。")
        max_side = body.get("max_side", 3200)
        if type(max_side) is not int or not 256 <= max_side <= 6000:
            raise ValueError("输出长边须在 256–6000 像素之间。")
        title = text_field(body, "title", 200)
        provenance = text_field(body, "provenance", 4000)
        with Image.open(self.base / "assets" / f"{source['id']}.png") as im:
            image = im.crop(crop).rotate(-angle, expand=True)
            image.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
            output = io.BytesIO()
            image.save(output, format="PNG")
        png = output.getvalue()
        config = {"source_id": source["id"], "crop": crop, "rotation": angle,
                  "width": image.width, "height": image.height, "image_sha256": digest(png)}
        version = digest(json.dumps(config, sort_keys=True).encode())[:24]
        (self.base / "assets" / f"{version}.png").write_bytes(png)
        rec = {**config, "version": version, "map_id": mid, "title": title,
               "provenance": provenance, "max_side": max_side, "created_at": stamp(),
               "coordinate_system": "image_pixels_top_left", "source_name": source["name"], "source_page": source["page"]}
        append(self.base / "maps.jsonl", rec)
        return self.detail(mid)

    @staticmethod
    def geometry(value, width, height):
        if not isinstance(value, dict) or value.get("type") not in {"point", "line", "polygon"}:
            raise ValueError("无效几何类型。")
        points = value.get("coordinates")
        if not isinstance(points, list) or not 1 <= len(points) <= 2000:
            raise ValueError("顶点数量无效。")
        for p in points:
            if not isinstance(p, list) or len(p) != 2 or any(type(v) not in (int, float) or not math.isfinite(v) for v in p):
                raise ValueError("顶点必须是有限的像素坐标。")
        validate_geometry(value["type"], points, width, height)
        return {"type": value["type"], "coordinates": points}

    def save_gold(self, mid, body):
        current = self.detail(mid)
        active = current["active"]
        if not active or body.get("map_version") != active["version"]:
            raise Conflict("底图版本已改变，请重新打开事件。")
        eid = body.get("event_id")
        event = next((e for e in current["events"] if e["id"] == eid), None)
        if event is None:
            raise KeyError(eid)
        if "base_revision" not in body or body["base_revision"] != event["revision"]:
            raise Conflict("标注已更新，请重新打开事件。")
        status = body.get("status")
        if status not in {"accepted", "ambiguous", "unlocatable", "rejected", "outside_map"}:
            raise ValueError("请选择审核状态。")
        evidence = text_field(body, "evidence")
        annotator = text_field(body, "annotator", 100)
        feature = body.get("geo_feature_type")
        if feature not in {k for k, _ in FEATURE_TYPES}:
            raise ValueError("要素类型不在统一词表中。")
        geometry = body.get("geometry")
        if geometry is not None:
            geometry = self.geometry(geometry, active["width"], active["height"])
        if status == "accepted" and geometry is None:
            raise ValueError("通过的事件必须有几何标注。")
        if status == "outside_map" and geometry:
            raise ValueError("范围外事件应清空几何标注。")
        tolerance = None
        if geometry and geometry["type"] in {"point", "line"}:
            tolerance = body.get("tolerance_px")
            if type(tolerance) not in (float, int) or not math.isfinite(tolerance) or not 0 <= tolerance <= max(active["width"], active["height"]):
                raise ValueError("无效像素容差。")
        record = {"schema_version": 1, "map_id": mid, "map_version": active["version"],
                  "image_sha256": active["image_sha256"], "event_id": eid, "status": status,
                  "geometry": geometry, "evidence": evidence, "annotator": annotator,
                  "geo_feature_type": feature, "tolerance_px": tolerance,
                  "coordinate_system": "image_pixels_top_left", "width": active["width"],
                  "height": active["height"], "created_at": stamp()}
        append(self.base / "gold.jsonl", record)
        return self.detail(mid)

    def restore(self, mid, body):
        current = self.detail(mid)
        if "base_revision" not in body or body["base_revision"] != current["revision"]:
            raise Conflict("底图已更新，请刷新。")
        old = next((r for r in current["history"] if r["version"] == body.get("version")), None)
        if old is None:
            raise ValueError("未知底图版本。")
        append(self.base / "maps.jsonl", {**old, "created_at": stamp(), "restored": True})
        return self.detail(mid)

    def asset_path(self, sid):
        allowed = {r["id"] for r in load_jsonl(self.base / "sources.jsonl")}
        allowed.update(r["version"] for r in load_jsonl(self.base / "maps.jsonl"))
        if sid not in allowed:
            raise KeyError(sid)
        return self.base / "assets" / f"{sid}.png"

    def prediction(self, mid, body):
        current = self.detail(mid)
        active = current["active"]
        if not active or body.get("map_version") != active["version"]:
            raise Conflict("预测对应的底图版本不一致。")
        model = text_field(body, "model", 200)
        rows = body.get("predictions")
        if not isinstance(rows, list) or not 1 <= len(rows) <= len(current["events"]):
            raise ValueError("预测数量无效。")
        records, seen = [], set()
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("预测必须是对象。")
            eid = row.get("event_id")
            if eid not in self.groups[mid]["events"]:
                raise ValueError("未知事件。")
            if eid in seen:
                raise ValueError("预测事件重复。")
            seen.add(eid)
            geom = row.get("geometry")
            if geom is not None:
                geom = self.geometry(geom, active["width"], active["height"])
            records.append({"map_id": mid, "map_version": active["version"], "event_id": eid,
                            "model": model, "geometry": geom, "created_at": stamp()})
        for row in records:
            append(self.base / "predictions.jsonl", row)
        return self.detail(mid)

    def export(self, mid, kind):
        current = self.detail(mid)
        active = current["active"]
        if not active:
            raise ValueError("请先保存标注底图。")
        png = self.asset_path(active["version"]).read_bytes()
        if digest(png) != active["image_sha256"]:
            raise ValueError("底图校验失败。")
        if kind == "gold":
            records = list(self.labels(mid, active["version"]).values())
            return json.dumps({"map": active, "annotations": records}, ensure_ascii=False, indent=2).encode()
        # Allowlist only: neither reference maps nor evidence/gold metadata enter this archive.
        rows = []
        for event in current["events"]:
            if not event["gold"] or event["gold"]["status"] != "accepted":
                continue
            rows.append({"event_id": event["id"], "map_version": active["version"],
                         "image": "map.png", "width": active["width"], "height": active["height"],
                         "text": event["text"], "question": event["question"]})
        if not rows:
            raise ValueError("当前底图没有已通过事件，无法导出评测输入。")
        prompt = ("Locate the event specified by the question using the passage and the map. "
                  "Return JSON with event_id and geometry: {type: point|line|polygon, coordinates: [[x,y],...]}. "
                  "Use original image pixels, origin at top left, x rightward, y downward. "
                  "Use one vertex for a point, at least two for a line, at least three for a polygon. "
                  "Return geometry: null if the supplied materials do not support localization.")
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("map.png", png)
            archive.writestr("tasks.jsonl", "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
            archive.writestr("prompt.txt", prompt)
            archive.writestr("manifest.json", json.dumps({"map_version": active["version"],
                "image_sha256": active["image_sha256"], "coordinate_system": "image_pixels_top_left",
                "event_count": len(rows)}))
        return output.getvalue()

    def overlay(self, mid, eid, kind, model=None):
        current = self.detail(mid)
        active = current["active"]
        if not active or eid not in self.groups[mid]["events"]:
            raise KeyError(eid)
        if kind not in {"gold", "predictions"}:
            raise ValueError("未知叠加层。")
        if kind == "predictions" and model is not None:
            row = self.model_predictions(mid, active["version"]).get(eid, {}).get(model)
        else:
            row = self.labels(mid, active["version"], kind).get(eid)
        if not row or not row.get("geometry"):
            raise ValueError("该事件没有可绘制的标注。")
        with Image.open(self.asset_path(active["version"])) as im:
            im = im.convert("RGB")
            draw = ImageDraw.Draw(im)
            pts = [tuple(p) for p in row["geometry"]["coordinates"]]
            style = None if kind == "gold" else prediction_style(row["model"])
            color = "#cf3f49" if style is None else style["color"]
            width = max(2, round(max(im.size)/700))
            if row["geometry"]["type"] == "point":
                x, y = pts[0]
                radius = width * 3
                draw.ellipse((x-radius,y-radius,x+radius,y+radius), fill=color, outline="white", width=width)
            elif row["geometry"]["type"] == "line":
                draw.line(pts, fill=color, width=width)
            else:
                draw.line(pts + [pts[0]], fill=color, width=width)
            metadata = PngImagePlugin.PngInfo()
            if style is not None:
                metadata.add_text("model", row["model"])
                metadata.add_text("event_id", eid)
                metadata.add_text("map_version", active["version"])
                caption = f"{eid} | {row['model']}".encode("ascii", "replace").decode()
                # Keep the label in the result copy, never in the clean model input.
                columns = max(1, (im.width - 12) // 7)
                for index, start in enumerate(range(0, len(caption), columns)):
                    line = caption[start:start + columns]
                    y = 4 + index * 14
                    draw.rectangle((2, y, min(im.width - 1, 10 + len(line) * 7), y + 14), fill="white")
                    draw.text((6, y), line, fill=color)
            out = io.BytesIO()
            im.save(out, format="PNG", pnginfo=metadata)
            return out.getvalue()
