#!/usr/bin/env python3
"""Qwen3.8-27B "no none option" ablation (2026-11-28): score the 75 re-run items and the 260 with them swapped in.

Inputs (package benchmark/exports/eval_v2_20261119):
  final260_20261126/runs/qwen3.8-27b-4bit.raw.jsonl     main run (prompt grounding-v2-20261119), 75 answered none
  rerun_nonone_20261128/runs/qwen3.8-27b-4bit.raw.jsonl  the 75 re-run with grounding-v2-nonone-20261128
  benchmark/diagnostics/difficulty_cue_20261126/item_levels.csv  difficulty level 1/2/3 of the 260 items

Writes (in the package, next to the re-run):
  rerun_nonone_20261128/runs/qwen3.8-27b-4bit-nonone260{,-lenient}.raw.jsonl / .pred.json / .score_polygon.json
      260 rows = 185 main-run rows + 75 re-run rows ("source" says which)
  final260_20261126 is not modified; the main-run lenient baseline goes to rerun_nonone_20261128/runs/
      qwen3.8-27b-4bit-main260-lenient.*
and in this folder: results.json, item_results.csv.

Parsing: "strict" = convert_predictions.py unchanged. "lenient" = the unified parser (lenient.py ->
code/make_lenient_final260.py), applied identically to the
main run and the re-run before convert_predictions.py. Scoring: eval_geometry.py, gold/gold_polygon.jsonl,
line_rules.csv (same as merge_final260.py). Statistics: bootstrap percentile 95% CI (10 000, seed 0),
Kruskal-Wallis (tie-corrected, df 2), Jonckheere-Terpstra (one-sided decreasing, 10 000 permutations).

Run from the repo root:  python3 benchmark/diagnostics/qwen_nonone_20261128/analyze.py
"""
import csv
import json
import math
import random
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PKG = ROOT / "benchmark/exports/eval_v2_20261119"
HERE = Path(__file__).resolve().parent
FINAL = PKG / "final260_20261126"
RERUN = PKG / "rerun_nonone_20261128"
sys.path.insert(0, str(PKG / "code"))
sys.path.insert(0, str(HERE))
import convert_predictions as cp  # noqa: E402
from lenient import lenient_raw, LENIENT_RULE  # noqa: E402

ids = (PKG / "runs/ids_260.txt").read_text().split()
nonone_ids = (RERUN / "ids.txt").read_text().split()
assert len(ids) == 260 and len(nonone_ids) == 75 and set(nonone_ids) <= set(ids)
level = {r["event_id"]: int(r["level"]) for r in csv.DictReader(open(ROOT / "benchmark/diagnostics/difficulty_cue_20261126/item_levels.csv"))}
assert set(level) == set(ids)
tasks = {t["event_id"]: t for t in map(json.loads, open(FINAL / "tasks.jsonl"))}


def rows_by_id(path):
    out = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            if r.get("error") is None:
                out[r["event_id"]] = r
    return out


main = rows_by_id(FINAL / "runs/qwen3.8-27b-4bit.raw.jsonl")
new = rows_by_id(RERUN / "runs/qwen3.8-27b-4bit.raw.jsonl")
assert set(new) == set(nonone_ids), f"re-run incomplete: {len(new)}/75"
for e in nonone_ids:
    assert cp.extract_json(main[e]["raw"])["type"] == "none"


def write_and_score(name, rows, tasks_path):
    p = RERUN / "runs" / f"{name}.raw.jsonl"
    p.write_text("".join(json.dumps(rows[e], ensure_ascii=False) + "\n" for e in ids), encoding="utf-8")
    pred, score = p.with_suffix("").with_suffix(".pred.json"), p.with_suffix("").with_suffix(".score_polygon.json")
    subprocess.run([sys.executable, str(PKG / "code/convert_predictions.py"), "--raw", str(p), "--tasks", str(tasks_path),
                    "--out", str(pred)], check=True, stdout=subprocess.DEVNULL, cwd=PKG)
    subprocess.run([sys.executable, str(PKG / "code/eval_geometry.py"), "--gold", "gold/gold_polygon.jsonl", "--pred", str(pred),
                    "--line-rules", "line_rules.csv", "--out", str(score)], check=True, stdout=subprocess.DEVNULL, cwd=PKG)
    return {e["event_id"]: e for e in json.load(open(score))["events"]}, {p["event_id"]: p for p in json.load(open(pred))["predictions"]}


def lenient_rows(rows):
    out = {}
    for e, r in rows.items():
        raw, fix = lenient_raw(r.get("raw"), tasks[e]["width"], tasks[e]["height"])
        out[e] = dict(r, raw=raw, **({"lenient_fix": fix, "raw_original": r.get("raw")} if fix else {}))
    return out


swapped = {e: dict(new[e], source=str(RERUN.relative_to(PKG) / "runs/qwen3.8-27b-4bit.raw.jsonl")) if e in new
           else dict(main[e], source=str(FINAL.relative_to(PKG) / "runs/qwen3.8-27b-4bit.raw.jsonl")) for e in ids}
mainrows = {e: main[e] for e in ids}
# the scorer only reads event_id / width / height from tasks; final260 tasks has all 260
VARIANTS = {
    "main_strict": (FINAL / "runs/qwen3.8-27b-4bit.score_polygon.json", FINAL / "runs/qwen3.8-27b-4bit.pred.json"),
    "main_lenient": write_and_score("qwen3.8-27b-4bit-main260-lenient", lenient_rows(mainrows), FINAL / "tasks.jsonl"),
    "nonone_strict": write_and_score("qwen3.8-27b-4bit-nonone260", swapped, FINAL / "tasks.jsonl"),
    "nonone_lenient": write_and_score("qwen3.8-27b-4bit-nonone260-lenient", lenient_rows(swapped), FINAL / "tasks.jsonl"),
}
p0, q0 = VARIANTS["main_strict"]
VARIANTS["main_strict"] = ({e["event_id"]: e for e in json.load(open(p0))["events"]},
                           {p["event_id"]: p for p in json.load(open(q0))["predictions"]})

rng = random.Random(0)


def boot(v, fn, n=10000):
    m = len(v)
    b = sorted(fn([v[rng.randrange(m)] for _ in range(m)]) for _ in range(n))
    return [b[int(0.025 * n)], b[int(0.975 * n) - 1]]


def mean(v):
    return sum(v) / len(v) if v else None


def median(v):
    v = sorted(v)
    n = len(v)
    return None if not n else (v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2)


def kruskal(groups):
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


def jt(groups):
    s = 0.0
    for a in range(len(groups)):
        for b in range(a + 1, len(groups)):
            for x in groups[a]:
                for y in groups[b]:
                    s += 1 if x > y else 0.5 if x == y else 0
    return s


def jt_perm(groups, n_perm=10000):
    obs = jt(groups); pool = [v for g in groups for v in g]; sizes = [len(g) for g in groups]; ge = 0
    for _ in range(n_perm):
        rng.shuffle(pool); gs = []; k = 0
        for s in sizes:
            gs.append(pool[k:k + s]); k += s
        ge += jt(gs) >= obs - 1e-9
    return (ge + 1) / (n_perm + 1)


def status(p):
    if p.get("error"):
        return "unparseable"
    return p["geometry"]["type"] if p.get("geometry") else "none"


def summary(sev, pred, items, ci=True):
    ev = [sev[e] for e in items]
    iou = [x["iou"] for x in ev]
    h5 = [float(x["hit@0.5"]) for x in ev]
    pir = [float(bool(x["point_in_region"])) for x in ev]
    dist = [x["centroid_dist_norm"] for x in ev if x.get("centroid_dist_norm") is not None]
    st = {}
    for e in items:
        k = status(pred[e]); st[k] = st.get(k, 0) + 1
    out = {"n": len(items), "IoU": mean(iou), "hit@0.5": mean(h5), "hit@0.75": mean([float(x["hit@0.75"]) for x in ev]),
           "center_in_region": mean(pir), "n_with_pred": len(dist),
           "median_center_dist_pct": 100 * median(dist) if dist else None,
           "within5pct": sum(d <= 0.05 for d in dist) / len(items),
           "boundary_iou_polygon": mean([x.get("boundary_iou", 0.0) for x in ev if x["gold_type"] == "polygon"]),
           "iou_gt0": sum(v > 0 for v in iou), "status": st}
    if ci:
        out["IoU_ci"] = boot(iou, mean)
        out["hit@0.5_ci"] = boot(h5, mean)
        out["center_in_region_ci"] = boot(pir, mean)
        if dist:
            out["median_center_dist_pct_ci"] = [100 * v for v in boot(dist, median)]
    return out


def by_level(sev, pred, items):
    res = {}
    for lv in (1, 2, 3):
        res[lv] = summary(sev, pred, [e for e in items if level[e] == lv])
    groups = [[sev[e]["iou"] for e in items if level[e] == lv] for lv in (1, 2, 3)]
    h, p = kruskal(groups)
    res["IoU_kw_p"], res["IoU_jt_p_decreasing"] = p, jt_perm(groups)
    groups = [[float(bool(sev[e]["point_in_region"])) for e in items if level[e] == lv] for lv in (1, 2, 3)]
    res["center_kw_p"], res["center_jt_p_decreasing"] = kruskal(groups)[1], jt_perm(groups, 2000)
    return res


results = {"meta": {"lenient_rule": LENIENT_RULE, "n_items": 260, "n_rerun": 75,
                    "rerun_prompt_version": json.loads(open(RERUN / "tasks.jsonl").readline())["prompt_version"]}}
for name, (sev, pred) in VARIANTS.items():
    results[name] = {"all260": summary(sev, pred, ids), "rerun75": summary(sev, pred, nonone_ids),
                     "other185": summary(sev, pred, [e for e in ids if e not in set(nonone_ids)], ci=False),
                     "by_level_260": by_level(sev, pred, ids),
                     "by_level_75": {lv: summary(sev, pred, [e for e in nonone_ids if level[e] == lv], ci=False) for lv in (1, 2, 3)}}

# paired: 260 swapped vs main (difference comes only from the 75)
for mode in ("strict", "lenient"):
    a, b = VARIANTS[f"main_{mode}"][0], VARIANTS[f"nonone_{mode}"][0]
    d = [b[e]["iou"] - a[e]["iou"] for e in ids]
    results[f"delta_260_{mode}"] = {"IoU": mean(d), "IoU_ci": boot(d, mean)}

# re-run reply facts
fin = {}
for e in nonone_ids:
    r = new[e]
    fin[r.get("finish_reason")] = fin.get(r.get("finish_reason"), 0) + 1
toks = [new[e]["usage"]["completion_tokens"] for e in nonone_ids if new[e].get("usage")]
results["rerun_replies"] = {"finish_reason": fin, "max_completion_tokens": max(toks) if toks else None,
                            "median_prompt_tokens": median([new[e]["usage"]["prompt_tokens"] for e in nonone_ids]),
                            "time_utc": [min(new[e]["time_utc"] for e in nonone_ids), max(new[e]["time_utc"] for e in nonone_ids)],
                            "image_max_pixels_used": sum(bool(new[e].get("image_max_pixels")) for e in nonone_ids)}
gt = {}
for e in nonone_ids:
    sev = VARIANTS["nonone_lenient"][0][e]
    k = (sev["gold_type"], status(VARIANTS["nonone_lenient"][1][e]))
    gt["/".join(k)] = gt.get("/".join(k), 0) + 1
results["rerun75_gold_vs_pred_type_lenient"] = gt

(HERE / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=1))
with open(HERE / "item_results.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["event_id", "level", "category", "gold_type", "raw_nonone", "status_strict", "status_lenient",
                "iou_strict", "iou_lenient", "hit@0.5", "center_in_region", "center_dist_pct"])
    for e in nonone_ids:
        ss, ps = VARIANTS["nonone_strict"]; sl, pl = VARIANTS["nonone_lenient"]
        d = sl[e].get("centroid_dist_norm")
        w.writerow([e, level[e], tasks[e]["category"], sl[e]["gold_type"], (new[e]["raw"] or "").strip()[:300],
                    status(ps[e]), status(pl[e]), round(ss[e]["iou"], 4), round(sl[e]["iou"], 4),
                    int(sl[e]["hit@0.5"]), int(bool(sl[e]["point_in_region"])), None if d is None else round(100 * d, 3)])
print(json.dumps({k: results[k]["rerun75"] if k in VARIANTS else None for k in VARIANTS}, ensure_ascii=False)[:1500])
