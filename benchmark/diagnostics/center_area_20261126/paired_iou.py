#!/usr/bin/env python3
"""Paired IoU differences between the closed models on the final 260 items (2026-11-26).

Sign-flip permutation test (two-sided, 10 000 draws) and bootstrap 95% CI (2 000 resamples) of the mean
per-item IoU difference; random.Random(0). Run from the repo root:
    .venv/bin/python benchmark/diagnostics/center_area_20261126/paired_iou.py
"""
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FINAL = ROOT / "benchmark/exports/eval_v2_20261119/final260_20261126"
ids = sorted((ROOT / "benchmark/exports/eval_v2_20261119/runs/ids_260.txt").read_text().split())


def iou(m):
    return {e["event_id"]: e["iou"] for e in json.load(open(FINAL / f"runs/{m}.score_polygon.json"))["events"]}


S, C, G = iou("gpt-6.2-sol"), iou("claude-opus-5-5"), iou("gemini-4-neon-low")
rng = random.Random(0)


def paired(a, b):
    d = [a[e] - b[e] for e in ids]
    obs = sum(d) / len(d)
    ge = sum(abs(sum(x if rng.random() < .5 else -x for x in d) / len(d)) >= abs(obs) - 1e-12 for _ in range(10000))
    bs = sorted(sum(rng.choice(d) for _ in d) / len(d) for _ in range(2000))
    return {"mean_diff": round(obs, 4), "ci95": [round(bs[50], 4), round(bs[1949], 4)], "p_perm": round((ge + 1) / 10001, 4)}


out = {"Gemini - Sol": paired(G, S), "Sol - Claude": paired(S, C), "Gemini - Claude": paired(G, C)}
print(json.dumps(out, ensure_ascii=False, indent=1))
(Path(__file__).resolve().parent / "paired_iou.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
