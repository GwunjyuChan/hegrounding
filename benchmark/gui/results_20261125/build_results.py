#!/usr/bin/env python3
"""Build the static eval results page (2026-11-25): results.html + results_20261125.json.

No model calls. Run from the repo root with the repo venv (do NOT use uv run):

    .venv/bin/python benchmark/gui/results_20261125/build_results.py

Inputs (all existing files):
  runs/<model>.score_polygon.json, runs/<model>.pred.json, runs/<model>.raw.jsonl   (eval_v2_20261119 package)
  gold/gold_polygon.jsonl, tasks.jsonl, line_rules.csv                               (same package)
  benchmark/diagnostics/center_area_20261125/{item_metrics.csv,results.json}
  benchmark/diagnostics/difficulty_cue_20261125/item_levels.csv                     (260 items, levels)
  benchmark/gui/home_v2/review_patch/review.html                                    (map image asset names)
Output: benchmark/gui/results_20261125/dist/{results.html,results_20261125.json}

Map images are not copied: the page loads them from the review site's existing content-addressed
assets, review/images/<sha256>.<ext>, relative to the /experiment/ homepage.
"""
import csv
import json
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
B = ROOT / "benchmark"
PKG = B / "exports/eval_v2_20261119"
CA = B / "diagnostics/center_area_20261125"
HERE = Path(__file__).resolve().parent
OUT = HERE / "dist"
DATA_NAME = "results_20261125.json"
MODELS = [("gpt-6.2-sol", "Sol"), ("qwen3.8-27b-4bit", "Qwen"), ("gemma-4-26b-q4", "Gemma"),
          ("gemma-4-26b-q4-lenient", "Gemma宽松")]
CAT_ZH = {"napoleonic_war": "拿破仑战争", "war_20th_century": "一战", "social_political": "社会政治",
          "disaster": "灾害", "public_health": "公共卫生", "epidemic": "疫病"}
N_BOOT, SEED = 10000, 0
rng = np.random.default_rng(SEED)


def jl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def fnum(v):
    if v in ("", "None", None):
        return None
    if v in ("True", "False"):
        return v == "True"
    try:
        return float(v)
    except ValueError:
        return v


def boot_mean(v):
    v = np.asarray(v, dtype=float)
    if len(v) < 2:
        return None
    s = np.sort(v[rng.integers(0, len(v), size=(N_BOOT, len(v)))].mean(1))
    return [round(float(s[int(0.025 * N_BOOT)]), 4), round(float(s[int(0.975 * N_BOOT) - 1]), 4)]


def r4(x):
    return None if x is None else round(float(x), 4)


# ------------------------------------------------------------------ load
levels = {r["event_id"]: r for r in csv.DictReader(open(B / "diagnostics/difficulty_cue_20261125/item_levels.csv"))}
ids = list(levels)
assert len(ids) == 260
gold = {g["event_id"]: g for g in jl(PKG / "gold/gold_polygon.jsonl")}
tasks = {t["event_id"]: t for t in jl(PKG / "tasks.jsonl")}
items = {}
for r in csv.DictReader(open(CA / "item_metrics.csv", encoding="utf-8")):
    items[(r["event_id"], r["model"])] = {k: fnum(v) for k, v in r.items()}
ca = json.load(open(CA / "results.json", encoding="utf-8"))
score = {short: {e["event_id"]: e for e in json.load(open(PKG / f"runs/{m}.score_polygon.json"))["events"]}
         for m, short in MODELS}
preds = {short: {p["event_id"]: p for p in json.load(open(PKG / f"runs/{m}.pred.json"))["predictions"]}
         for m, short in MODELS}
review_html = (B / "gui/home_v2/review_patch/review.html").read_text(encoding="utf-8")
asset = {sha: f"review/images/{sha}.{ext}" for sha, ext in re.findall(r"images/([0-9a-f]{64})\.(png|jpg|jpeg|gif)", review_html)}
missing = sorted({tasks[e]["image_sha256"] for e in ids} - set(asset))
assert not missing, f"no review image asset for {missing}"

# ------------------------------------------------------------------ per-event rows
events = []
for eid in ids:
    g, t, lv = gold[eid], tasks[eid], levels[eid]
    sol = items[(eid, "Sol")]
    ev = {"id": eid, "category": t["category"], "category_zh": CAT_ZH[t["category"]], "category4": sol["category4"],
          "level": int(lv["level"]), "cue": lv["cue"], "scale": sol["scale_tier"], "shape": sol["shape"],
          "gold_type": sol["gold_type"], "lang": t["input_language"], "image": asset[t["image_sha256"]],
          "image_name": Path(g["image"]).name, "w": g["width"], "h": g["height"], "mpp": sol["metres_per_px"],
          "line_px": sol["line_half_width_px"], "question": t["question"], "text": t["model_input_text"],
          "gold": g["geometry"], "gold_center": [r4(sol["gold_cx"]), r4(sol["gold_cy"])], "models": {}}
    for _, short in MODELS:
        it, sc, p = items[(eid, short)], score[short][eid], preds[short].get(eid, {})
        ev["models"][short] = {
            "status": it["pred_status"], "geom": p.get("geometry"), "raw": (p.get("raw") or "")[:600],
            "iou": r4(sc["iou"]), "biou": r4(sc.get("boundary_iou")), "outcome": sc["outcome"],
            "center": [r4(it["pred_cx"]), r4(it["pred_cy"])] if it["has_pred"] else None,
            "dist_pct": r4(it["dist_pct"]), "dist_m": r4(it["dist_m"]), "hit5": bool(it["hit5"]),
            "recall": r4(it["recall"]), "precision": r4(it["precision"]), "area_ratio": r4(it["area_ratio"])}
    events.append(ev)

# ------------------------------------------------------------------ summary table (260 items)
summary = {}
for _, short in MODELS:
    es = [score[short][e] for e in ids]
    poly = [e for e in es if e["gold_type"] == "polygon"]
    g = ca["groups"][short]["全部:全部"]
    summary[short] = {
        "n": len(es), "mean_iou": r4(np.mean([e["iou"] for e in es])), "mean_iou_ci": boot_mean([e["iou"] for e in es]),
        "hit50": r4(np.mean([e["hit@0.5"] for e in es])), "hit50_ci": boot_mean([float(e["hit@0.5"]) for e in es]),
        "biou": r4(np.mean([e.get("boundary_iou", 0.0) for e in poly])), "n_poly": len(poly),
        "dist_pct_median": r4(g["全部题型"]["dist_pct"]["median"]), "dist_pct_ci": g["全部题型"]["dist_pct"]["median_ci"],
        "dist_m_median": r4(g["全部题型"]["dist_m"]["median"]), "dist_m_ci": g["全部题型"]["dist_m"]["median_ci"],
        "n_dist_m": g["全部题型"]["n_dist_m"],
        "hit5": r4(g["全部题型"]["hit5"]["rate"]), "hit5_ci": g["全部题型"]["hit5"]["ci"],
        "poly_recall": r4(g["面状"]["recall"]["mean"]), "poly_recall_ci": g["面状"]["recall"]["ci"],
        "poly_precision": r4(g["面状"]["precision"]["mean"]), "poly_precision_ci": g["面状"]["precision"]["ci"],
        "line_recall": r4(g["线状"]["recall"]["mean"]), "line_recall_ci": g["线状"]["recall"]["ci"],
        "line_precision": r4(g["线状"]["precision"]["mean"]), "line_precision_ci": g["线状"]["precision"]["ci"],
        "no_pred": g["全部题型"]["n_no_pred"],
        "n_none": sum(e["outcome"] == "false_abstention" for e in es),
        "n_invalid": sum(e["outcome"] == "invalid_prediction" for e in es)}

# ------------------------------------------------------------------ grouped metrics with 95% CI
GROUPINGS = {"难度": ("level", lambda e: f"第{e['level']}档", ["第1档", "第2档", "第3档"]),
             "类别": ("category4", lambda e: e["category4"], ["武装冲突", "社会政治", "灾害", "公共卫生"]),
             "尺度": ("scale", lambda e: e["scale"], ["局地", "区域", "国家"]),
             "形状": ("shape", lambda e: e["shape"], ["矩形", "多边形", "线"])}
SUBTYPES = {"全部题型": lambda e: True, "面状": lambda e: e["gold_type"] == "polygon", "线状": lambda e: e["gold_type"] == "line"}
groups = {}
for gname, (_, key, order) in GROUPINGS.items():
    groups[gname] = {"order": order, "data": {}}
    for _, short in MODELS:
        for val in order:
            for st, sf in SUBTYPES.items():
                sub = [e for e in events if key(e) == val and sf(e)]
                if not sub:
                    continue
                c = ca["groups"][short][f"{gname}:{val}"][st]
                ious = [e["models"][short]["iou"] for e in sub]
                hits = [float(score[short][e["id"]]["hit@0.5"]) for e in sub]
                groups[gname]["data"][f"{short}|{val}|{st}"] = {
                    "n": len(sub), "no_pred": c["n_no_pred"],
                    "iou": [r4(np.mean(ious)), boot_mean(ious)], "hit50": [r4(np.mean(hits)), boot_mean(hits)],
                    "dist_pct": [r4(c["dist_pct"]["median"]), c["dist_pct"]["median_ci"]],
                    "hit5": [r4(c["hit5"]["rate"]), c["hit5"]["ci"]],
                    "recall": [r4(c["recall"]["mean"]), c["recall"]["ci"]],
                    "precision": [r4(c["precision"]["mean"]), c["precision"]["ci"]],
                    "area_ratio": [r4(c["area_ratio"]["median"]), c["area_ratio"]["median_ci"]]}
    print(gname, "done", file=sys.stderr)

data = {"built": "2026-11-25", "package": "eval_v2_20261119", "models": [s for _, s in MODELS],
        "model_ids": {s: m for m, s in MODELS}, "summary": summary, "groups": groups, "events": events,
        "level_tests": ca["level_tests"], "scale_missing_items": ca["meta"]["scale_missing_items"],
        "scale_missing_maps": ca["meta"]["scale_missing_maps"], "n_boot": N_BOOT}
OUT.mkdir(exist_ok=True)
(OUT / DATA_NAME).write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
html = (HERE / "template.html").read_text(encoding="utf-8").replace("__DATA_URL__", DATA_NAME)
(OUT / "results.html").write_text(html, encoding="utf-8")
print(json.dumps({"events": len(events), "json_bytes": (OUT / DATA_NAME).stat().st_size,
                  "html_bytes": (OUT / "results.html").stat().st_size}))
