#!/usr/bin/env python3
"""Center distance and area precision / recall for the 2026-11-19 runs on the 260-item set (2026-11-25).

No model calls. Run from the repo root with the repo venv (do NOT use uv run):

    .venv/bin/python benchmark/diagnostics/center_area_20261125/compute.py

Inputs
  items      .deploy/difficulty_20261125/model_inputs_v2_20261119.jsonl (excluded = false -> 260),
             cross-checked against benchmark/diagnostics/difficulty_cue_20261125/item_levels.csv (level, category)
  gold       benchmark/exports/eval_v2_20261119/gold/gold_polygon.jsonl (same gold as runs/*.score_polygon.json)
  preds      runs/<model>.raw.jsonl, converted with code/convert_predictions.py (asserted equal to runs/<model>.pred.json)
  line rule  benchmark/line_rules_v2_20261119.csv (== package line_rules.csv), via eval_geometry.attach_line_rules
  scale      metres/px: benchmark/map_scales.csv, then line_rules_v2_20261119.csv, then
             difficulty_scale_20261121/map_extent_estimates.csv (long side km / long side px);
             maps marked schematic -> missing. Scale tier: difficulty_scale_20261121/item_labels.csv.

Masks are built exactly as eval_geometry.score_event does (asserted: mask IoU == score file IoU):
gold line -> buffered with the map's line rule, the prediction (box or line) with the same half-width;
gold polygon -> filled, a predicted line buffered at the default 1% of the diagonal.
"""
import csv
import importlib.util
import json
import math
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
B = ROOT / "benchmark"
PKG = B / "exports/eval_v2_20261119"
HERE = Path(__file__).resolve().parent
MODELS = {"gpt-6.2-sol": "Sol", "qwen3.8-27b-4bit": "Qwen", "gemma-4-26b-q4": "Gemma",
          "gemma-4-26b-q4-lenient": "Gemma宽松"}
CAT4 = {"napoleonic_war": "武装冲突", "war_20th_century": "武装冲突", "social_political": "社会政治",
        "disaster": "灾害", "public_health": "公共卫生", "epidemic": "公共卫生"}
SCALE = {"1_local": "局地", "2_regional": "区域", "3_national": "国家"}
N_BOOT, N_PERM, SEED = 10000, 10000, 0
HIT_PCT = 5.0


def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


eg = load_mod("eval_geometry_pkg", PKG / "code/eval_geometry.py")
cp = load_mod("convert_predictions_pkg", PKG / "code/convert_predictions.py")


def jl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


# ------------------------------------------------------------------ items and labels
mi = jl(ROOT / ".deploy/difficulty_20261125/model_inputs_v2_20261119.jsonl")
inc = [r["event_id"] for r in mi if not r.get("excluded")]
levels = {r["event_id"]: r for r in csv.DictReader(open(B / "diagnostics/difficulty_cue_20261125/item_levels.csv"))}
assert len(inc) == 260 and set(inc) == set(levels), "260-item set mismatch"
tasks = {t["event_id"]: t for t in jl(PKG / "tasks.jsonl")}
gold = {g["event_id"]: g for g in jl(PKG / "gold/gold_polygon.jsonl")}
eg.attach_line_rules(gold, eg.load_line_rules(B / "line_rules_v2_20261119.csv"))
scale_lab = {r["event_id"]: r for r in csv.DictReader(open(B / "diagnostics/difficulty_scale_20261121/item_labels.csv"))}

# metres per pixel
mpp_known, schematic = {}, set()
for f in ("map_scales.csv", "line_rules_v2_20261119.csv"):
    for r in csv.DictReader(open(B / f)):
        b = os.path.basename(r["image"])
        if r.get("metres_per_px") and b not in mpp_known:
            mpp_known[b] = (float(r["metres_per_px"]), f)
        if "schematic" in (r.get("rule", "") + r.get("how_measured", "")).lower():
            schematic.add(b)
est = {r["image"]: r for r in csv.DictReader(open(B / "diagnostics/difficulty_scale_20261121/map_extent_estimates.csv"))}
for b, r in est.items():
    if "schematic" in (r.get("note") or "").lower():
        schematic.add(b)


def metres_per_px(g):
    b = os.path.basename(g["image"])
    if b in schematic:
        return None, "schematic"
    if b in mpp_known:
        return mpp_known[b][0], mpp_known[b][1]
    r = est[b]
    return float(r["long_side_km"]) * 1000 / max(g["width"], g["height"]), "estimate:" + r["confidence"]


def shape(geom):
    if geom["type"] == "line":
        return "线"
    pts = geom["coordinates"]
    xs = {round(p[0], 1) for p in pts}
    ys = {round(p[1], 1) for p in pts}
    return "矩形" if len(pts) == 4 and len(xs) == 2 and len(ys) == 2 else "多边形"


# ------------------------------------------------------------------ geometric centres
def geo_center(geom):
    pts = np.asarray(geom["coordinates"], dtype=float)
    if geom["type"] == "polygon":
        x, y = pts[:, 0], pts[:, 1]
        x1, y1 = np.roll(x, -1), np.roll(y, -1)
        cr = x * y1 - x1 * y
        a = cr.sum() / 2
        if abs(a) > 1e-9:
            return float(((x + x1) * cr).sum() / (6 * a)), float(((y + y1) * cr).sum() / (6 * a))
        return float(x.mean()), float(y.mean())
    if geom["type"] == "line":
        seg = np.hypot(*np.diff(pts, axis=0).T)
        if seg.sum() > 0:
            mid = (pts[:-1] + pts[1:]) / 2
            return tuple(float(v) for v in (mid * seg[:, None]).sum(0) / seg.sum())
    return float(pts[:, 0].mean()), float(pts[:, 1].mean())


# ------------------------------------------------------------------ per item, per model
def convert(model):
    latest = {}
    for r in jl(PKG / f"runs/{model}.raw.jsonl"):
        if r["event_id"] not in latest or latest[r["event_id"]].get("error"):
            latest[r["event_id"]] = r
    out = {}
    for eid, r in latest.items():
        t = tasks[eid]
        try:
            if r.get("error"):
                raise ValueError("api error")
            geom = cp.to_geometry(cp.extract_json(r["raw"]), t["width"], t["height"])
            status = geom["type"] if geom else "none"
        except (ValueError, KeyError, TypeError):
            geom, status = None, "unparseable"
        out[eid] = (geom, status)
    ref = {p["event_id"]: p.get("geometry") for p in json.load(open(PKG / f"runs/{model}.pred.json"))["predictions"]}
    for eid, (geom, _) in out.items():
        assert geom == ref.get(eid), f"{model} {eid}: conversion differs from pred.json"
    return out


rows = []
for model, short in MODELS.items():
    preds = convert(model)
    sev = {e["event_id"]: e for e in json.load(open(PKG / f"runs/{model}.score_polygon.json"))["events"]}
    for eid in inc:
        g = gold[eid]
        w, h = g["width"], g["height"]
        diag = math.hypot(w, h)
        gg = eg.validate(g["geometry"])
        geom, status = preds.get(eid, (None, "missing"))
        mpp, mpp_src = metres_per_px(g)
        lv = levels[eid]
        row = {"event_id": eid, "model": short, "level": int(lv["level"]), "category": tasks[eid]["category"],
               "category4": CAT4[tasks[eid]["category"]], "scale_tier": SCALE[scale_lab[eid]["scale_tier_km"]],
               "gold_type": gg["type"], "shape": shape(gg), "width": w, "height": h,
               "metres_per_px": mpp, "mpp_source": mpp_src, "pred_status": status,
               "has_pred": geom is not None}
        params = {}
        if gg["type"] == "line":
            params["line_half_width_px"] = g["line_rule_px"]
            row["line_half_width_px"] = round(g["line_rule_px"], 3)
        G = eg.to_mask(gg, w, h, **params)
        row["gold_area_px"] = int(G.sum())
        gx, gy = geo_center(gg)
        if geom is not None:
            pg = eg.validate(geom)
            P = eg.to_mask(pg, w, h, **params)
            inter = int(np.logical_and(P, G).sum())
            pa = int(P.sum())
            union = int(np.logical_or(P, G).sum())
            iou = inter / union if union else 0.0
            assert abs(iou - sev[eid]["iou"]) < 1e-9, (model, eid, iou, sev[eid]["iou"])
            px, py = geo_center(pg)
            d = math.hypot(px - gx, py - gy)
            row.update(pred_type=pg["type"], pred_area_px=pa, inter_px=inter, iou=iou,
                       precision=(inter / pa) if pa else None, recall=inter / row["gold_area_px"],
                       area_ratio=pa / row["gold_area_px"], dist_px=d, dist_pct=100 * d / diag,
                       dist_m=(d * mpp) if mpp else None, hit5=(100 * d / diag) <= HIT_PCT,
                       pred_cx=px, pred_cy=py)
        else:
            assert sev[eid]["iou"] == 0.0
            row.update(pred_type=None, pred_area_px=None, inter_px=None, iou=0.0, precision=None, recall=0.0,
                       area_ratio=None, dist_px=None, dist_pct=None, dist_m=None, hit5=False, pred_cx=None, pred_cy=None)
        row.update(gold_cx=gx, gold_cy=gy)
        rows.append(row)

# ------------------------------------------------------------------ statistics
rng = np.random.default_rng(SEED)


def boot_ci(v, fn):
    v = np.asarray(v, dtype=float)
    if len(v) < 2:
        return None
    idx = rng.integers(0, len(v), size=(N_BOOT, len(v)))
    s = np.sort(fn(v[idx]))
    return [float(s[int(0.025 * N_BOOT)]), float(s[int(0.975 * N_BOOT) - 1])]


med = lambda a: np.median(a, axis=-1)
mean = lambda a: np.mean(a, axis=-1)


def q(v, p):
    return float(np.percentile(v, p)) if len(v) else None


def summarise(items):
    n = len(items)
    pr = [r for r in items if r["has_pred"]]
    dp = [r["dist_pct"] for r in pr]
    dm = [r["dist_m"] for r in pr if r["dist_m"] is not None]
    rec = [r["recall"] for r in items]
    prec = [r["precision"] for r in pr if r["precision"] is not None]
    ar = [r["area_ratio"] for r in pr]
    hit = [float(r["hit5"]) for r in items]
    s = {"n": n, "n_no_pred": n - len(pr), "n_pred_zero_area": sum(r["precision"] is None for r in pr),
         "n_dist_m": len(dm), "n_scale_missing_among_pred": len(pr) - len(dm),
         "dist_pct": {"median": q(dp, 50), "q1": q(dp, 25), "q3": q(dp, 75), "mean": float(np.mean(dp)) if dp else None,
                      "median_ci": boot_ci(dp, med)},
         "dist_m": {"median": q(dm, 50), "q1": q(dm, 25), "q3": q(dm, 75), "mean": float(np.mean(dm)) if dm else None,
                    "median_ci": boot_ci(dm, med)},
         "hit5": {"rate": float(np.mean(hit)) if hit else None, "ci": boot_ci(hit, mean)},
         "recall": {"mean": float(np.mean(rec)), "median": q(rec, 50), "ci": boot_ci(rec, mean)},
         "precision": {"mean": float(np.mean(prec)) if prec else None, "median": q(prec, 50), "n": len(prec),
                       "ci": boot_ci(prec, mean)},
         "area_ratio": {"median": q(ar, 50), "q1": q(ar, 25), "q3": q(ar, 75), "median_ci": boot_ci(ar, med),
                        "share_gt1": float(np.mean([a > 1 for a in ar])) if ar else None}}
    return s


def kruskal(groups):  # same as difficulty_cue_20261125/analyze.py (tie-corrected, chi2 df=2)
    allv = sorted((v, gi) for gi, g in enumerate(groups) for v in g)
    n = len(allv); ranks = [0.0] * n; i = 0; tie = 0
    while i < n:
        j = i
        while j + 1 < n and allv[j + 1][0] == allv[i][0]:
            j += 1
        for k in range(i, j + 1):
            ranks[k] = (i + j) / 2 + 1
        t = j - i + 1; tie += t ** 3 - t; i = j + 1
    rs = [0.0] * len(groups)
    for (v, gi), rk in zip(allv, ranks):
        rs[gi] += rk
    h = 12 / (n * (n + 1)) * sum(r ** 2 / len(g) for r, g in zip(rs, groups)) - 3 * (n + 1)
    c = 1 - tie / (n ** 3 - n)
    h = h / c if c > 0 else 0.0
    return h, math.exp(-h / 2)


def jt_perm(groups):
    """Jonckheere-Terpstra, one-sided 'level 1 >= 2 >= 3' (pairs earlier > later, ties 0.5); permutation p.

    Same statistic as difficulty_cue_20261125/analyze.py, vectorised: JT = sum_{i,j} C[i,j] [lab_i < lab_j].
    """
    v = np.array([x for g in groups for x in g], dtype=float)
    lab = np.repeat(np.arange(len(groups)), [len(g) for g in groups])
    C = (v[:, None] > v[None, :]) + 0.5 * (v[:, None] == v[None, :])
    up = np.triu(np.ones((len(groups),) * 2), 1)

    def stat(L):  # L: (k, n) label rows
        M = np.eye(len(groups))[L]                # k, n, g
        A = np.einsum("kig,ij,kjh->kgh", M, C, M, optimize=True)  # k, g, g
        return (A * up).sum((1, 2))

    obs = stat(lab[None])[0]
    ge = 0
    for _ in range(N_PERM // 500):
        L = np.array([rng.permutation(lab) for _ in range(500)])
        ge += int((stat(L) >= obs - 1e-9).sum())
    return float(obs), (ge + 1) / (N_PERM + 1)


def level_tests(items):
    """Higher value = better for every metric (distance negated), so JT tests 'worse with higher level'."""
    defs = {"中心距离%（仅有预测）": lambda r: -r["dist_pct"] if r["has_pred"] else None,
            "中心距离%（无预测记最远）": lambda r: -r["dist_pct"] if r["has_pred"] else -1e9,
            "命中≤5%": lambda r: float(r["hit5"]),
            "召回率": lambda r: r["recall"],
            "精确率": lambda r: r["precision"] if r["has_pred"] else None}
    out = {}
    for name, f in defs.items():
        groups = [[f(r) for r in items if r["level"] == l and f(r) is not None] for l in (1, 2, 3)]
        if min(len(g) for g in groups) < 2:
            continue
        h, p = kruskal(groups)
        _, jp = jt_perm(groups)
        raw = [[abs(x) if name.startswith("中心") and x > -1e8 else x for x in g] for g in groups]
        out[name] = {"n": [len(g) for g in groups],
                     "median": [float(np.median([x for x in g if x > -1e8])) if g else None for g in raw],
                     "mean": [float(np.mean([x for x in g if x > -1e8])) for g in raw],
                     "kw_H": h, "kw_p": p, "jt_p_worse_with_level": jp}
    return out


GROUPINGS = {"全部": lambda r: "全部", "难度": lambda r: f"第{r['level']}档", "类别": lambda r: r["category4"],
             "尺度": lambda r: r["scale_tier"], "形状": lambda r: r["shape"]}
results = {"meta": {"items": len(inc), "models": MODELS, "n_boot": N_BOOT, "n_perm": N_PERM, "seed": SEED,
                    "hit_threshold_pct_diag": HIT_PCT},
           "groups": {}, "level_tests": {}}
for short in MODELS.values():
    mr = [r for r in rows if r["model"] == short]
    results["groups"][short] = {}
    for gname, key in GROUPINGS.items():
        for val in sorted({key(r) for r in mr}):
            sub = [r for r in mr if key(r) == val]
            results["groups"][short][f"{gname}:{val}"] = {
                "全部题型": summarise(sub),
                "面状": summarise([r for r in sub if r["gold_type"] == "polygon"]) if any(r["gold_type"] == "polygon" for r in sub) else None,
                "线状": summarise([r for r in sub if r["gold_type"] == "line"]) if any(r["gold_type"] == "line" for r in sub) else None}
    results["level_tests"][short] = {"全部": level_tests(mr),
                                     "面状": level_tests([r for r in mr if r["gold_type"] == "polygon"]),
                                     "线状": level_tests([r for r in mr if r["gold_type"] == "line"])}
    print(short, "done", file=sys.stderr)

sol = [r for r in rows if r["model"] == "Sol"]
results["meta"]["scale_missing_items"] = sum(r["metres_per_px"] is None for r in sol)
results["meta"]["scale_missing_maps"] = sorted({os.path.basename(gold[r["event_id"]]["image"]) for r in sol if r["metres_per_px"] is None})
results["meta"]["mpp_source_items"] = {s: sum(r["mpp_source"] == s for r in sol) for s in sorted({r["mpp_source"] for r in sol})}
results["meta"]["counts"] = {k: {v: sum(GROUPINGS[k](r) == v for r in sol) for v in sorted({GROUPINGS[k](r) for r in sol})}
                             for k in GROUPINGS}
results["meta"]["gold_type"] = {t: sum(r["gold_type"] == t for r in sol) for t in ("polygon", "line")}

cols = ["event_id", "model", "level", "category", "category4", "scale_tier", "gold_type", "shape", "width", "height",
        "metres_per_px", "mpp_source", "line_half_width_px", "pred_status", "has_pred", "pred_type", "gold_area_px",
        "pred_area_px", "inter_px", "iou", "precision", "recall", "area_ratio", "gold_cx", "gold_cy", "pred_cx", "pred_cy",
        "dist_px", "dist_pct", "dist_m", "hit5"]
with open(HERE / "item_metrics.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in ((k, r.get(k)) for k in cols)})
(HERE / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(results["meta"], ensure_ascii=False))
