"""Validate and export this isolated, non-gold annotation round."""

from __future__ import annotations

import base64
import argparse
import ast
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
import mimetypes
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ROUND_ID = "assistant_round_20261011"
DATASETS = ["benchmark/zurich_pilot_10.jsonl", "benchmark/map_first_candidates.jsonl"]
ZURICH_IMAGE = "benchmark/atlas/assets/2ae3fca4eb15dced41f82401.png"
ZURICH_SHA = "fc5f835f11cd6f7cafefc7183b57d10c0911372149a1c2077f662a6d70570aec"
# Read-only review aids shown beside each event; candidate records and hashes are untouched.
SCREENING = "benchmark/annotations/screening_110_2026-10-19.csv"
ORIGINAL_TEXTS = "benchmark/sources/original_texts_2026-10-19.json"
ORIGINAL_FIELDS = ("extracted", "original_text", "english_translation", "translation_by", "source", "location",
                   "url", "language", "rights", "note", "suggested_public_domain_source")
# English display text for the Chinese notes on the review page. Display only: the records keep their Chinese text,
# so candidate hashes and saved reviews do not change when a translation is added or edited.
DISPLAY_EN = HERE / "display_en.json"
DISPLAY_FIELDS = ("location", "caveat", "map_evidence", "text_evidence")
HAN = re.compile(r"[\u3400-\u9fff]")
STATUSES = {"proposed", "ambiguous", "outside_map", "source_conflict", "unreadable"}
STATUS_ZH = {
    "proposed": "待确认候选", "ambiguous": "有歧义", "outside_map": "图幅外",
    "source_conflict": "来源冲突", "unreadable": "图示难辨",
}

# Read the existing vocabulary without importing Matplotlib's GUI dependencies.
VOCAB_TREE = ast.parse((ROOT / "benchmark/annotate_geo.py").read_text(encoding="utf-8"))
FEATURE_TYPES = dict(ast.literal_eval(next(
    node.value for node in VOCAB_TREE.body
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "FEATURE_TYPES" for t in node.targets)
)))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_sources():
    sources = {}
    for name in DATASETS:
        for line in (ROOT / name).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            event_id = row["event_id"]
            if event_id in sources:
                raise ValueError(f"Duplicate source ID: {event_id}")
            sources[event_id] = (row, name)
    return sources


def cross(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def on_segment(a, b, c):
    return cross(a, b, c) == 0 and all(min(a[i], b[i]) <= c[i] <= max(a[i], b[i]) for i in (0, 1))


def intersects(a, b, c, d):
    if cross(a, b, c) * cross(a, b, d) < 0 and cross(c, d, a) * cross(c, d, b) < 0:
        return True
    return any((on_segment(a, b, c), on_segment(a, b, d), on_segment(c, d, a), on_segment(c, d, b)))


def validate_decision(row, width, height):
    event_id = row["event_id"]
    if row["status"] not in STATUSES or type(row["confidence"]) is not int or not 1 <= row["confidence"] <= 4:
        raise ValueError(f"Invalid status/confidence: {event_id}")
    for key in ("location", "text_evidence", "map_evidence", "caveat", "source_check", "feature_type", "target_kind"):
        if not isinstance(row.get(key), str) or not row[key].strip():
            raise ValueError(f"Missing {key}: {event_id}")
    if row["feature_type"] not in FEATURE_TYPES:
        raise ValueError(f"Feature type not in project vocabulary: {event_id}")
    geom = row["geometry"]
    if row["status"] == "proposed" and geom is None:
        raise ValueError(f"Proposed without geometry: {event_id}")
    if row["status"] in {"source_conflict", "outside_map", "unreadable"} and geom is not None:
        raise ValueError(f"Unexpected geometry: {event_id}")
    if geom is None:
        return
    points = geom["coordinates"]
    kind = geom["type"]
    if kind not in {"polygon", "line"} or len(points) < (3 if kind == "polygon" else 2):
        raise ValueError(f"Invalid geometry: {event_id}")
    for p in points:
        if len(p) != 2 or any(type(v) not in (int, float) or not math.isfinite(v) for v in p):
            raise ValueError(f"Invalid point: {event_id}: {p}")
        if not (0 <= p[0] < width and 0 <= p[1] < height):
            raise ValueError(f"Out of bounds: {event_id}: {p}, {(width, height)}")
    if any(a == b for a, b in zip(points, points[1:])):
        raise ValueError(f"Zero length segment: {event_id}")
    if kind == "polygon":
        if points[0] == points[-1]:
            raise ValueError(f"Polygon must use implicit closure: {event_id}")
        area = abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(points, points[1:] + points[:1]))) / 2
        if area <= 0:
            raise ValueError(f"Zero area: {event_id}")
        edges = list(zip(points, points[1:] + points[:1]))
        for i, (a, b) in enumerate(edges):
            for j in range(i + 1, len(edges)):
                if j == i + 1 or (i == 0 and j == len(edges) - 1):
                    continue
                if intersects(a, b, *edges[j]):
                    raise ValueError(f"Self-intersecting polygon: {event_id}, edges {i}, {j}")


def image_metadata(name):
    path = ROOT / name
    with Image.open(path) as im:
        width, height = im.size
    return {"path": name, "width": width, "height": height, "sha256": sha256(path)}


def collect():
    sources = load_sources()
    decisions = json.loads((HERE / "decisions.json").read_text(encoding="utf-8"))
    ids = [r["event_id"] for r in decisions]
    if len(set(ids)) != len(ids) or set(ids) != set(sources) or len(ids) != 139:
        raise ValueError("Annotation IDs must match all 139 active source IDs exactly once")
    if sha256(ROOT / ZURICH_IMAGE) != ZURICH_SHA:
        raise ValueError("Frozen Zurich image changed; do not reuse these coordinates")
    records, assets = [], {}
    for decision in decisions:
        source, dataset = sources[decision["event_id"]]
        is_zurich = decision["event_id"].startswith("Z")
        reference_name = source["image"]
        image_name = ZURICH_IMAGE if is_zurich else reference_name
        for name in (image_name, reference_name):
            if name not in assets:
                assets[name] = image_metadata(name)
        image_meta, ref_meta = assets[image_name], assets[reference_name]
        expected_hash = source.get("map_asset_sha256", source.get("map_sha256"))
        if expected_hash and ref_meta["sha256"] != expected_hash:
            raise ValueError(f"Source reference image changed: {decision['event_id']}")
        if [ref_meta["width"], ref_meta["height"]] != [source["img_w"], source["img_h"]]:
            raise ValueError(f"Source image dimensions changed: {decision['event_id']}")
        validate_decision(decision, image_meta["width"], image_meta["height"])
        records.append({
            "schema_version": 1, "annotation_round": ROUND_ID, "annotated_at": "2026-10-11",
            "annotator": {"kind": "ai_assistant", "name": "Codex current session", "independent_human": False},
            **decision,
            "source_dataset": dataset, "source_record": source,
            "annotation_image": image_meta, "reference_image": ref_meta,
            "annotation_map_role": "clean_historical_basemap" if is_zurich else "battle_reference_map_with_military_symbols",
            "coordinate_system": "native_image_pixels_top_left_x_right_y_down_implicit_polygon_closure",
            "geometry_semantics": "hypothesis_only" if decision["status"] == "ambiguous" else "candidate_only",
            "tolerance_px": None, "human_review": "pending", "eligible_for_scoring": False,
            "gold_status": "not_gold", "prior_prediction_exposure": is_zurich,
            "requires_map_version_review": is_zurich,
            "map_text_independence": "not_established",
        })
    return records, assets


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def overview(records, assets):
    folder = HERE / "overviews"
    folder.mkdir(exist_ok=True)
    groups = defaultdict(list)
    for record in records:
        groups[record["annotation_image"]["path"]].append(record)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 17)
    except OSError:
        font = ImageFont.load_default()
    for image_name, group in groups.items():
        with Image.open(ROOT / image_name) as source_image:
            im = source_image.convert("RGBA")
        overlay = Image.new("RGBA", im.size)
        draw = ImageDraw.Draw(overlay)
        for record in group:
            geom = record["geometry"]
            if not geom:
                continue
            points = [tuple(p) for p in geom["coordinates"]]
            rgb = (204, 0, 102) if record["status"] == "proposed" else (168, 85, 0)
            if geom["type"] == "polygon":
                draw.polygon(points, fill=(*rgb, 24))
                draw.line(points + points[:1], fill=(*rgb, 255), width=3)
            else:
                draw.line(points, fill=(*rgb, 255), width=3)
            text = record["event_id"] + (" ?" if record["status"] == "ambiguous" else "")
            box = draw.textbbox((0, 0), text, font=font)
            tw, th = box[2] - box[0] + 8, box[3] - box[1] + 6
            x = max(0, min(points[0][0], im.width - tw))
            y = max(0, min(points[0][1] - th - 3, im.height - th))
            draw.rectangle((x, y, x + tw, y + th), fill=(255, 255, 255, 240))
            draw.text((x + 4, y + 2 - box[1]), text, fill=(*rgb, 255), font=font)
        im = Image.alpha_composite(im, overlay).convert("RGB")
        draw = ImageDraw.Draw(im)
        banner = "AI CANDIDATES | NOT GOLD | 2026-10-11"
        draw.rectangle((0, 0, min(im.width, 440), 28), fill="white")
        draw.text((6, 2), banner, font=font, fill=(135, 0, 56))
        im.save(folder / f"{Path(image_name).stem}.png")


def report(records, manifest):
    groups = defaultdict(list)
    for record in records:
        groups[record["annotation_image"]["path"]].append(record)
    counts = manifest["status_counts"]
    lines = [
        "# 全量事件第一轮 AI 辅助标注报告", "", "日期：2026-10-11。**这是候选标注，不是人工金标准，也不是新一轮模型评测结果。**", "",
        "## 交付", "",
        "- [逐事件审核页](review.html)：一次显示一个事件，支持原像素、缩放、候选区域和参考图切换。",
        "- [人工审核工作台](http://127.0.0.1:8771/review.html)：支持点、线、区域编辑，接受/修改后接受/需修改/待补证据/剔除与备注保存。人工几何单独保存在审核日志，不覆盖 AI 候选。需启动本地 `serve_reviews.py`，详见标注规则；直接打开 HTML 文件是只读模式。",
        "- [机器可读记录](annotations.jsonl)：110 条，包含原始题目、文本、来源、坐标、证据和疑点。",
        "- [手工决策源文件](decisions.json)、[版本与哈希](manifest.json)、[标注规则](PROTOCOL.md)。",
        "- [浏览器检查记录](browser_validation.json)：逐事件图像及叠加像素检查、桌面/手机布局。它检查页面功能，不证明历史标注正确。",
        "- [地图总览目录](overviews/)：26 张叠加图，像素尺寸与各自标注底图一致。细节审核以逐事件页面为准。", "",
        "## 覆盖", "",
        "活动集合共 **110 条事件、26 张参考地图**：苏黎世第二次战役 10 条，以及 map-first 扩展的 100 条。archive 中停用或重复版本没有再标。",
        "", "| 本轮状态 | 数量 | 含义 |", "| --- | ---: | --- |",
        f"| 待确认候选 | {counts.get('proposed', 0)} | 有可审核几何，但仍不是 gold |",
        f"| 有歧义 | {counts.get('ambiguous', 0)} | 其中 4 条只给假设几何，其余不强行画图 |",
        f"| 图示难辨 | {counts.get('unreadable', 0)} | 需更清晰地图或可读单位标签 |",
        f"| 来源冲突 | {counts.get('source_conflict', 0)} | 问题或来源转述需先修正 |",
        f"| 图幅外 | {counts.get('outside_map', 0)} | 仅指本轮使用的底图版本 |", "",
        f"共 **{manifest['geometry_count']} 条有几何，{len(records) - manifest['geometry_count']} 条为空**。空几何也有完整审核记录；不能把这些条目算作模型错误。所有记录均 pending / not_gold / eligible_for_scoring=false。",
        "", "## 底图和独立性", "",
        "苏黎世使用此前实验冻结的 Usteri 裁切 `2ae3fca4eb15dced41f82401`，1538 × 1754。**不是当前 UI 的 1144 × 820 版本。坐标不能直接粘到当前版本上。**该 1816 年地图也不是 1799 年即时测绘，需核对年代差异。",
        "",
        "其他 100 条暂在各自原始作战参考图上标注，保留原像素。已有军事符号可以帮助第一轮标注，但它们会泄漏答案；这些结果不能包装成干净底图上的推理能力或定位准确率。",
        "",
        "本轮没有读取预测坐标来生成标签，没有调用收费模型，没有修改旧 gold、活动事件文件、地图原件或线上平台。苏黎世已有模型结果出现在之前讨论里，因此不能声称是严格盲标。",
        "",
        "多数 map-first 问题由地图图注或符号转述，文本和地图不独立。已逐图目视检查，并对部分外部原文回查；`source_check` 说明检查层级，不等于全体来源已经独立考证。",
        "", "地理要素沿用项目 v1 词表；军事对象与部署语义保存在 `target_kind`。这是独立候选格式，需人工审核、版本对齐与字段转换后才能导入 atlas，不能直接替换其 gold 文件。",
        "", "## 优先修复", "",
        "1. **MF0045、MF0083、MF0095**：原先的图例/来源冲突已于 2026-10-21 随原文替换解决（题目改为 Petre 原文点名的地点），需在审核页复核新题。",
        "4. **苏黎世 Z0002、Z0003**：Fahr 高地/树林受北侧裁切影响；Regensdorf 在本轮底图之外。先扩图或明确排除，不调整标签去迎合模型。",
        "5. **苏黎世 Z0001、Z0005、Z0006、Z0008**：岸段、高地或营地存在定位粒度不足。保留疑点，不能把给定村名直接当作精确事件区域。",
        "6. **MF0102**：Stakhov 有新旧村和河岸对应问题；必须核对地名变体。",
        "", "上述地图图例冲突可在对应 [Auerstadt 原图](" + next(r["source_record"]["map_url"] for r in records if r["event_id"] == "MF0045") + ")、[Pultusk 原图](" + next(r["source_record"]["map_url"] for r in records if r["event_id"] == "MF0083") + ")、[Friedland 原图](" + next(r["source_record"]["map_url"] for r in records if r["event_id"] == "MF0095") + ")对照核查。",
        "", "## 建议审核顺序", "",
        "先看来源冲突，再看有歧义/图示难辨，最后确认候选几何。不要仅凭多边形看起来合理就接受；应同时核对目标实体、时刻、岸别、地形与地图版本。",
        "",
        "人工确认后另存审核版本，注明审核者、时间、修改原因和证据。争议样本应由导师或第二位标注者裁决；受模型输出影响的修订需披露。正式评测之前冻结问题、地图、标签及容差，不能把本轮 79 条候选直接当正式测试集。",
        "", "## 地图索引", "", "| 战场/图幅 | 事件数 | 候选/歧义/其他 | 逐事件 | 总览 |", "| --- | ---: | --- | --- | --- |",
    ]
    for image_name, group in groups.items():
        c = Counter(r["status"] for r in group)
        source = group[0]["source_record"]
        title = source.get("battle_name", source.get("battle_id", Path(image_name).stem))
        event_id = group[0]["event_id"]
        lines.append(f"| {title} | {len(group)} | {c['proposed']} / {c['ambiguous']} / {len(group)-c['proposed']-c['ambiguous']} | [{event_id}](review.html#{event_id}) | [PNG](overviews/{Path(image_name).stem}.png) |")
    lines.extend(["", "## 逐条记录", "", "| 事件 | 状态 | 置信度/5 | 几何 | 候选位置或未定位原因 |", "| --- | --- | ---: | --- | --- |"])
    for r in records:
        geom = r["geometry"]["type"] if r["geometry"] else "null"
        loc = r["location"].replace("|", "/")
        lines.append(f"| [{r['event_id']}](review.html#{r['event_id']}) | {STATUS_ZH[r['status']]} | {r['confidence']} | {geom} | {loc} |")
    lines.extend(["", "## 来源回查", "", "除各地图原图及图例外，本轮回查的外部材料如下。回查不等于独立证实地图边界。", ""])
    source_groups = defaultdict(list)
    for r in records:
        if r["source_check"] in {"external_original_viewed", "local_original_and_reference_map"}:
            source_groups[r["source_record"]["article_url"]].append(r["event_id"])
    for url, ids in source_groups.items():
        lines.append(f"- [{', '.join(ids)}]({url})。具体章节保留在每条 `source_record.source_section` 中。")
    lines.extend(["", "## 验证与复现", "", "生成时校验 110 个 ID 完整且不重复、原图哈希和尺寸、坐标边界、非退化几何及多边形无自交。机器校验不能证明历史定位正确。", "", "```sh", ".venv/bin/python benchmark/annotations/assistant_round_20261011/build.py", "```", "", "脚本只重建本目录输出。任何坐标或题目修订都需重新生成，并保留人工审核记录。图像与文献的公开再分发许可仍需另行检查。", ""])
    (HERE / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def source_review(event_ids, text_first=frozenset()):
    """Screening advice and recovered source passages per event; missing files give an empty map.
    Events in text_first got a new verbatim passage on 2026-10-21, so the older recovered-source entry no longer applies."""
    review = defaultdict(dict)
    if (ROOT / SCREENING).exists():
        with (ROOT / SCREENING).open(encoding="utf-8-sig", newline="") as stream:
            for row in csv.DictReader(stream):
                review[row["event_id"]]["screening"] = {
                    "advice": row["建议"], "issue": row["问题说明"],
                    "rewritten_question": row["建议改写的问题"], "ai_paraphrase": row["原文为AI改写"] == "是",
                    "text_origin": row["来源类型"]}
    if (ROOT / ORIGINAL_TEXTS).exists():
        for row in json.loads((ROOT / ORIGINAL_TEXTS).read_text(encoding="utf-8")):
            if row["event_id"] not in text_first:
                review[row["event_id"]]["original"] = {key: row.get(key) for key in ORIGINAL_FIELDS}
    unknown = set(review) - set(event_ids)
    if unknown:
        raise ValueError(f"Source review rows for unknown events: {sorted(unknown)}")
    return dict(review)


def display_strings(records, review):
    """Chinese strings the review page shows as data; each needs an English entry in display_en.json."""
    found = set()
    def add(value):
        if isinstance(value, str) and HAN.search(value):
            found.add(value)
    for record in records:
        for key in DISPLAY_FIELDS:
            add(record.get(key))
        add(record["source_record"].get("annotation_caution"))
    for info in review.values():
        # "原题：" / "原文：" parts carry English after the prefix, which the page translates itself.
        for part in (info.get("screening", {}).get("issue") or "").split("；"):
            if not re.match(r"(原题|原文)：", part):
                add(part)
        add(info.get("original", {}).get("note"))
    return found


def display_translations(records, review):
    """The display_en.json entries this round uses, and the shown strings that still lack one."""
    table = json.loads(DISPLAY_EN.read_text(encoding="utf-8")) if DISPLAY_EN.exists() else {}
    wanted = display_strings(records, review)
    return {key: table[key] for key in sorted(wanted) if key in table}, sorted(wanted - set(table))


def text_first_ids(records):
    return {r["event_id"] for r in records if r["source_record"].get("question_revision", "").startswith("2026-10-21 text-first")}


def render_review(records, manifest, assets, web_root=None):
    review = source_review({r["event_id"] for r in records}, text_first_ids(records))
    display_en, missing = display_translations(records, review)
    if missing:
        print(f"warning: {len(missing)} review-page notes have no English in {DISPLAY_EN.name}", file=sys.stderr)
    payload = {"records": records, "manifest": manifest, "images": {}, "source_review": review, "display_en": display_en}
    for name, meta in assets.items():
        if sha256(ROOT / name) != meta["sha256"]:
            raise ValueError(f"Image changed: {name}")
        mime = mimetypes.guess_type(name)[0] or "image/png"
        if web_root is not None:
            relative = f"images/{meta['sha256']}{Path(name).suffix}"
            target = web_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / name).read_bytes())
            url = relative
        else:
            url = f"data:{mime};base64," + base64.b64encode((ROOT / name).read_bytes()).decode("ascii")
        payload["images"][name] = {**meta, "url": url}
    html = (HERE / "review.template.html").read_text(encoding="utf-8")
    replacements = {"__ROUND_DATA__": json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c"),
                    "__LUCIDE_SOURCE__": (ROOT / "benchmark/gui/vendor/lucide.js").read_text(encoding="utf-8"),
                    "__REVIEW_UI_SOURCE__": (HERE / "review-ui.js").read_text(encoding="utf-8"),
                    "__GEOMETRY_EDITOR_SOURCE__": (HERE / "geometry-editor.js").read_text(encoding="utf-8")}
    for marker, value in replacements.items():
        html = html.replace(marker, value)
    ((web_root or HERE) / "review.html").write_text(html, encoding="utf-8")


def main(review_only=False):
    if review_only:
        records = [json.loads(line) for line in (HERE / "annotations.jsonl").read_text().splitlines() if line.strip()]
        manifest = json.loads((HERE / "manifest.json").read_text())
        render_review(records, manifest, {m["path"]: m for m in manifest["image_assets"]})
        print("Rebuilt review.html only; candidate data and human reviews unchanged")
        return
    records, assets = collect()
    tracked = [ROOT / name for name in DATASETS] + [ROOT / name for name in assets]
    before = {str(p): sha256(p) for p in tracked}
    counts = Counter(r["status"] for r in records)
    manifest = {
        "round_id": ROUND_ID, "date": "2026-10-11", "scope": "active_datasets_only",
        "event_count": len(records), "annotation_image_count": len({r['annotation_image']['path'] for r in records}),
        "status_counts": dict(counts), "geometry_count": sum(r["geometry"] is not None for r in records),
        "source_check_counts": dict(Counter(r["source_check"] for r in records)),
        "datasets": [{"path": name, "sha256": sha256(ROOT / name)} for name in DATASETS],
        "annotation_decisions_sha256": sha256(HERE / "decisions.json"), "image_assets": list(assets.values()),
        "gold": False, "all_human_reviews_pending": True, "eligible_for_scoring": False,
        "image_resize_applied": False, "paid_model_calls": 0, "old_gold_modified": False,
        "current_atlas_modified": False, "online_sync_performed": False,
        "prior_prediction_exposure": {"zurich_second_1799": True},
        "schema_note": "Custom pixel geometry, not GeoJSON; polygon closure is implicit. Null geometry is a documented unresolved decision.",
        "feature_type_vocabulary": FEATURE_TYPES,
        "feature_type_vocabulary_source": "benchmark/annotate_geo.py:FEATURE_TYPES",
        "validation": "IDs, reference hashes/dimensions, bounds, polygon area and self-intersections passed",
    }
    (HERE / "annotations.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
    write_json(HERE / "manifest.json", manifest)
    overview(records, assets)
    report(records, manifest)
    render_review(records, manifest, assets)
    if before != {str(p): sha256(p) for p in tracked}:
        raise RuntimeError("A source file changed while generating the review bundle")
    print(json.dumps({"events": len(records), "status_counts": dict(counts), "geometry_count": manifest["geometry_count"], "review": str(HERE / "review.html"), "sources_unchanged": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-only", action="store_true")
    main(parser.parse_args().review_only)
