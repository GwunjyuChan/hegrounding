"""Merge the 2026-10-21 text-first items into the review round (run from the repo root; idempotent).

Replacements (field `replaces`): the MF record keeps its ID; event_text/source_text become the verbatim public-domain
passage (or Claude's translation of one), the question is replaced (old one kept in target_question_previous), and the
decision gets the new evidence. Geometry is kept unless the spec says it was redrawn.
New items (MF0111+) are appended to map_first_candidates.jsonl and decisions.json, copying the map fields from an
existing record on the same image. Point drafts become small regions (QUESTION_GUIDELINES: all truth as regions).
Before the first run the touched files are copied to .deploy/pre_text_first_20261021/.
"""
import csv, glob, json, math, pathlib, re, shutil

DATA = pathlib.Path("benchmark/map_first_candidates.jsonl")
ROUND = pathlib.Path("benchmark/annotations/assistant_round_20261011")
DECISIONS = ROUND / "decisions.json"
SCREENING = pathlib.Path("benchmark/annotations/screening_110_2026-10-19.csv")
ITEMS = sorted(glob.glob("benchmark/sources/text_first/*_2026-10-21.jsonl"))
BACKUP = pathlib.Path(".deploy/pre_text_first_20261021")
REVISION = "2026-10-21 text-first: map-derived text replaced by a public-domain source passage; question rewritten to QUESTION_GUIDELINES v0.1"
TEXT_FIELDS = ("event_text", "source_text", "text_kind", "input_language", "source_language", "source_kind", "source_citation",
               "article_url", "source_rights", "source_rights_basis", "source_archive_id", "source_raw_file", "source_raw_sha256",
               "source_raw_lines", "source_raw_dropped_lines", "ocr_corrections", "translation_by", "translation_review",
               "source_evidence")
EVENT_KEYS = {"event_id", "place", "time", "event_text", "target_question", "article_url", "source_section", "suggested_geometry",
              "spatial_tags", "event_text_ai_paraphrase", "previous_article_url", "source_text", "input_language",
              "source_language", "source_citation", "source_rights", "target_question_previous", "question_revision",
              "text_kind", "source_kind", "translation_by", "translation_review", "event_text_previous"}
KINDS = {  # new items: (feature_type, target_kind)
    "MF0111": ("other", "deployment_sector"), "MF0112": ("other", "deployment_line"), "MF0113": ("other", "battery_position"),
    "MF0114": ("other", "deployment_line"), "MF0115": ("other", "deployment_sector"), "MF0116": ("other", "cavalry_sector"),
    "MF0117": ("other", "outpost"), "MF0118": ("other", "deployment_sector"), "MF0119": ("other", "deployment_sector"),
    "MF0120": ("building", "farm"), "MF0121": ("settlement", "settlement"), "MF0122": ("settlement", "settlement"),
    "MF0123": ("settlement", "settlement"), "MF0124": ("river", "channel_entrance"), "MF0125": ("high_ground", "post_area"),
    "MF0126": ("other", "reserve_area"),
    # second batch (Pelet): new items, and replaced items whose subject changed
    "MF0127": ("building", "castle"), "MF0128": ("road", "route"), "MF0129": ("settlement", "settlement"),
    "MF0130": ("settlement", "headquarters"), "MF0131": ("other", "route"), "MF0132": ("high_ground", "position"),
    "MF0133": ("high_ground", "position"), "MF0134": ("other", "rear_guard_position"), "MF0135": ("bridge", "bridge"),
    "MF0136": ("settlement", "settlement"), "MF0137": ("settlement", "settlement"),
    "MF0049": ("settlement", "post_area"), "MF0050": ("bridge", "causeway_and_bridge"), "MF0051": ("road", "route"),
    "MF0052": ("road", "route"), "MF0054": ("other", "route"), "MF0055": ("settlement", "settlement"),
    "MF0056": ("road", "deployment_line"), "MF0073": ("settlement", "headquarters"), "MF0074": ("building", "post_area"),
    "MF0075": ("settlement", "settlement"),
    # third batch (all remaining AI paraphrases replaced)
    "MF0013": ("building", "post_area"), "MF0014": ("other", "battery_position"), "MF0015": ("other", "battery_position"),
    "MF0138": ("other", "post_area"), "MF0139": ("high_ground", "battery_position"),
    "MF0005": ("settlement", "settlement"), "MF0006": ("settlement", "settlement"), "MF0007": ("settlement", "settlement"),
    "MF0008": ("bridge", "bridgehead"), "MF0021": ("bridge", "bridgehead"), "MF0022": ("other", "deployment_sector"),
    "MF0024": ("river", "deployment_sector"), "MF0037": ("settlement", "settlement"), "MF0038": ("settlement", "settlement"),
    "MF0039": ("bridge", "bridgehead"), "MF0040": ("settlement", "suburb"), "MF0041": ("other", "camp_area"),
    "MF0042": ("settlement", "settlement"), "MF0044": ("other", "outpost_line"), "MF0045": ("settlement", "settlement"),
    "MF0046": ("settlement", "settlement"), "MF0047": ("settlement", "settlement"), "MF0048": ("woodland", "position"),
    "MF0061": ("woodland", "wood"), "MF0062": ("road", "battery_position"), "MF0063": ("other", "deployment_sector"),
    "MF0076": ("other", "deployment_position"), "MF0077": ("settlement", "settlement"), "MF0078": ("settlement", "settlement"),
    "MF0079": ("road", "route"), "MF0080": ("settlement", "settlement"), "MF0081": ("other", "cavalry_sector"),
    "MF0083": ("road", "battery_position"), "MF0084": ("road", "route"), "MF0085": ("settlement", "settlement"),
    "MF0086": ("settlement", "settlement"), "MF0087": ("settlement", "settlement"), "MF0088": ("other", "fortification_line"),
    "MF0089": ("settlement", "settlement"), "MF0090": ("settlement", "battery_position"), "MF0091": ("settlement", "settlement"),
    "MF0092": ("settlement", "settlement"), "MF0093": ("settlement", "settlement"), "MF0094": ("woodland", "wood"),
    "MF0095": ("other", "deployment_sector"), "MF0096": ("settlement", "settlement"),
}

def region(geom, w, h):
    """Point draft -> regular octagon of radius 1.2% of the longer image side (implicit closure)."""
    if geom is None or geom["type"] != "point":
        return geom, None
    x, y = geom["coordinates"]; r = round(0.012 * max(w, h))
    pts = [[round(x + r * math.cos(k * math.pi / 4)), round(y + r * math.sin(k * math.pi / 4))] for k in range(8)]
    pts = [[min(max(px, 0), w - 1), min(max(py, 0), h - 1)] for px, py in pts]
    return {"type": "polygon", "coordinates": pts}, r

def main():
    if not BACKUP.exists():
        BACKUP.mkdir(parents=True)
        for p in (DATA, DECISIONS, SCREENING, ROUND / "annotations.jsonl", ROUND / "manifest.json", ROUND / "review.html",
                  ROUND / "REPORT.md", ROUND / "build.py", ROUND / "test_build.py"):
            shutil.copy2(p, BACKUP / p.name)
    rows = [json.loads(l) for l in DATA.read_text().splitlines() if l.strip()]
    by_id = {r["event_id"]: r for r in rows}
    decisions = json.loads(DECISIONS.read_text(encoding="utf-8"))
    dec_by_id = {d["event_id"]: d for d in decisions}
    with SCREENING.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f); fields = reader.fieldnames; srows = list(reader)
    scr_by_id = {s["event_id"]: s for s in srows}
    done = []
    for path in ITEMS:
        for l in open(path):
            it = json.loads(l); eid = it["event_id"]
            geom, radius = region(it["draft_geometry"], it["img_w"], it["img_h"])
            caveat = "几何为助手按原文和地图起草，需人工审核。" if geom else "原文所指地点不在这张图上（弃答题）：正确做法是不标注；需人工确认。"
            if radius:
                caveat += f"原文指一个点状地物，按半径约 {radius} 像素的小区域给出。"
            if it["geometry_source"].startswith("assistant_redraw"):
                caveat += "旧几何不符合原文所指位置，已重画。"
            if it.get("translation_by"):
                caveat += "模型看到的是 Claude 的英译，译文待审。"
            if eid in by_id and it.get("replaces") != eid and by_id[eid].get("text_first_created") != it["created"]:
                raise SystemExit(f"{eid} exists but the spec does not say it replaces it")
            if eid in by_id:
                r = by_id[eid]
                if r["image"] != it["image"]:
                    raise SystemExit(f"{eid}: image differs from the existing record")
                if it.get("replaces"):
                    r.setdefault("target_question_previous", r["target_question"])
                    r.setdefault("event_text_previous", r["event_text"])
            else:
                template = next(x for x in rows if x["image"] == it["image"] and not x["event_id"].startswith("MF01"))
                r = {k: v for k, v in template.items() if k not in EVENT_KEYS}
                r["event_id"] = eid; rows.append(r); by_id[eid] = r
            for k in TEXT_FIELDS:
                if it.get(k) is not None:
                    r[k] = it[k]
            r.update(target_question=it["target_question"], question_revision=REVISION, time=it["time"],
                     place=it["answer_zh"], event_text_ai_paraphrase=False, spatial_tags=it["spatial_tags"],
                     suggested_geometry=geom["type"] if geom else None, text_first_created=it["created"])
            d = dec_by_id.get(eid)
            if d is None:
                ft, tk = KINDS[eid]
                d = {"event_id": eid, "feature_type": ft, "target_kind": tk}
                decisions.append(d); dec_by_id[eid] = d
            elif eid in KINDS:
                d["feature_type"], d["target_kind"] = KINDS[eid]
            status = "proposed" if it["status"] == "pending" else it["status"]
            if not it.get("replaces") or it["geometry_source"].startswith("assistant_redraw") or d.get("geometry") is None:
                d["geometry"] = geom
            d.update(status=status, confidence=it["confidence_draft"], location=it["answer_zh"],
                     text_evidence=it["text_evidence"], map_evidence=it["map_evidence"], caveat=caveat,
                     source_check="verbatim_source_passage_and_map_viewed")
            s = scr_by_id.get(eid)
            if s is None:
                s = {k: "" for k in fields}; s["event_id"] = eid; s["battle"] = it["battle_id"]; srows.append(s); scr_by_id[eid] = s
                s["你的审核"] = "无记录"
            s.update({"来源类型": "叙述史料", "source_kind": it["source_kind"], "AI候选状态": status,
                      "建议": "已换原文并重写" if it.get("replaces") else "新题（先找原文再出题）",
                      "问题说明": f"原文：{it['source_citation']}" + ("（Claude 英译，待审）" if it.get("translation_by") else ""),
                      "原问题": it["target_question"], "建议改写的问题": "",
                      "原文为AI改写": "否（原文翻译）" if it.get("translation_by") else "否"})
            done.append(eid)
    DATA.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    DECISIONS.write_text("[\n" + ",\n".join("  " + json.dumps(d, ensure_ascii=False, separators=(",", ":")) for d in decisions)
                         + "\n]\n", encoding="utf-8")
    # The round's explicit event count grows with the new items (build.py check and test_build.py).
    n = len(decisions)
    for path, pats in ((ROUND / "build.py", (r"len\(ids\) != \d+", r"all \d+ active source IDs")),
                       (ROUND / "test_build.py", (r"self\.assertEqual\(len\(self\.records\), \d+\)",
                                                  r'self\.assertEqual\(len\(\{r\["event_id"\] for r in self\.records\}\), \d+\)',
                                                  r'if "screening" in review\[e\]\]\), \d+\)'))):
        text = path.read_text(encoding="utf-8")
        for pat in pats:
            text = re.sub(pat, lambda m: re.sub(r"\d+(?=\D*$)", str(n), m.group(0)), text)
        path.write_text(text, encoding="utf-8")
    with SCREENING.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fields); w.writeheader(); w.writerows(srows)
    print(len(done), "items applied:", " ".join(done))
    print("records", len(rows), "decisions", len(decisions), "screening rows", len(srows))

if __name__ == "__main__":
    main()
