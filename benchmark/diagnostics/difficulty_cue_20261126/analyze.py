"""[2026-11-26 copy: final 260-item runs in final260_20261126/, six model variants] Scores by location-cue level (1 direct, 2 convert, 3 relational) on the 260-item set.

No model calls. Inputs: eval_v2 score files, difficulty_reviews (latest difficulty_cue per event),
difficulty_overrides.json, model_inputs (excluded flag). Kruskal-Wallis (tie-corrected, chi2 df=2) and
Jonckheere-Terpstra (one-sided, decreasing with level; permutation p) per model and metric.
"""
import json, math, random, sys, csv
from pathlib import Path

R = Path(__file__).resolve().parents[3]
D = R / ".deploy/difficulty_20261125"
PKG = R / "benchmark/exports/eval_v2_20261119"
OUT = Path(__file__).resolve().parent
MODELS = {"gpt-6.2-sol": "Sol", "claude-opus-5-5": "Claude", "gemini-4-neon-low": "Gemini", "qwen3.8-27b-4bit": "Qwen", "gemma-4-26b-q4": "Gemma", "gemma-4-26b-q4-lenient": "Gemma宽松"}
MODELS = {m: s for m, s in MODELS.items() if (Path(__file__).resolve().parents[3] / f"benchmark/exports/eval_v2_20261119/final260_20261126/runs/{m}.score_polygon.json").exists()}
LV = {"direct": 1, "convert": 2, "relational": 3}
rng = random.Random(0)

mi = [json.loads(l) for l in open(D / "model_inputs_v2_20261119.jsonl")]
inc = [r["event_id"] for r in mi if not r.get("excluded")]
cue = {}
for r in sorted(map(json.loads, open(D / "difficulty_reviews_20261125.jsonl")), key=lambda r: r["reviewed_at"]):
    if r["kind"] == "difficulty_cue_20261123":
        cue[r["event_id"]] = r["cue"]
level = {e: LV[cue[e]] for e in inc}
for e, o in json.load(open(D / "difficulty_overrides.json")).items():
    if e in level:
        level[e] = int(o["level"])
tasks = {t["event_id"]: t for t in map(json.loads, open(PKG / "final260_20261126/tasks.jsonl"))}
ev = {m: {e["event_id"]: e for e in json.load(open(PKG / f"final260_20261126/runs/{m}.score_polygon.json"))["events"]} for m in MODELS}

METRICS = {"IoU": lambda e: e["iou"], "hit@0.5": lambda e: float(e["hit@0.5"]),
           "中心命中": lambda e: float(bool(e["point_in_region"]))}


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
    df = len(groups) - 1
    p = math.exp(-h / 2) if df == 2 else float("nan")
    return h, p


def jt(groups):  # count of pairs (earlier level > later level), ties 0.5
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


def boot(v, n=10000):
    m = len(v); b = sorted(sum(rng.choice(v) for _ in range(m)) / m for _ in range(n))
    return b[int(0.025 * n)], b[int(0.975 * n) - 1]


def analyse(ids, tag):
    res = {"subset": tag, "n_by_level": {l: sum(level[e] == l for e in ids) for l in (1, 2, 3)}, "models": {}}
    for m, short in MODELS.items():
        mr = {}
        for name, f in METRICS.items():
            groups = [[f(ev[m][e]) for e in ids if level[e] == l] for l in (1, 2, 3)]
            h, p = kruskal(groups)
            mr[name] = {"means": [sum(g) / len(g) for g in groups], "ci": [boot(g) for g in groups],
                        "kw_H": h, "kw_p": p, "jt_p_decreasing": jt_perm(groups, 2000 if name != "IoU" else 10000),
                        "monotone": all(sum(groups[i]) / len(groups[i]) >= sum(groups[i + 1]) / len(groups[i + 1]) for i in range(2))}
        allv = [ev[m][e] for e in ids]
        mr["overall"] = {"n": len(allv), "IoU": sum(e["iou"] for e in allv) / len(allv),
                         "hit@0.5": sum(e["hit@0.5"] for e in allv) / len(allv),
                         "hit@0.75": sum(e["hit@0.75"] for e in allv) / len(allv),
                         "中心命中": sum(bool(e["point_in_region"]) for e in allv) / len(allv),
                         "biou": (lambda P: (sum(e.get("boundary_iou", 0) for e in P) / len(P)) if P else None)([e for e in allv if e["gold_type"] == "polygon"]),
                         "none": sum(e["outcome"] == "false_abstention" for e in allv),
                         "invalid": sum(e["outcome"] == "invalid_prediction" for e in allv)}
        mr["none"] = [sum(ev[m][e]["outcome"] == "false_abstention" for e in ids if level[e] == l) for l in (1, 2, 3)]
        mr["biou_poly"] = [(lambda P: ((sum(ev[m][e].get("boundary_iou", 0) for e in P) / len(P)) if P else None, len(P)))(
            [e for e in ids if level[e] == l and ev[m][e]["gold_type"] == "polygon"]) for l in (1, 2, 3)]
        res["models"][short] = mr
    return res


subsets = {"全部 260 题": inc,
           "只算多边形": [e for e in inc if ev["gpt-6.2-sol"][e]["gold_type"] == "polygon"],
           "只算线": [e for e in inc if ev["gpt-6.2-sol"][e]["gold_type"] == "line"],
           "去掉 Qwen 答 none 的题": [e for e in inc if ev["qwen3.8-27b-4bit"][e]["outcome"] != "false_abstention"],
           "去掉拿破仑题": [e for e in inc if tasks[e]["category"] != "napoleonic_war"]}
out = {k: analyse(v, k) for k, v in subsets.items()}
comp = {l: {} for l in (1, 2, 3)}
for e in inc:
    c = tasks[e]["category"]; comp[level[e]][c] = comp[level[e]].get(c, 0) + 1
gt = {l: {} for l in (1, 2, 3)}
for e in inc:
    t = ev["gpt-6.2-sol"][e]["gold_type"]; gt[level[e]][t] = gt[level[e]].get(t, 0) + 1
out["_composition"] = {"category": comp, "geometry": gt}
with open(OUT / "item_levels.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["event_id", "level", "cue", "category", "gold_type"] + [f"{s.lower()}_iou" for s in MODELS.values()] + [f"{s.lower()}_outcome" for s in MODELS.values()])
    for e in inc:
        w.writerow([e, level[e], cue[e], tasks[e]["category"], ev["gpt-6.2-sol"][e]["gold_type"]]
                   + [round(ev[m][e]["iou"], 4) for m in MODELS] + [ev[m][e]["outcome"] for m in MODELS])
(OUT / "results.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
print(json.dumps(out, ensure_ascii=False)[:200])
