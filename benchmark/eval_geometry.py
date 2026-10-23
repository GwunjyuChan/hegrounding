"""Unified region scoring for point / line / polygon event grounding.

Every gold and predicted geometry is converted to a pixel region on the
annotation image, then scored with IoU:

- polygon: filled interior (implicit closure)
- line:    polyline buffered by a half-width proportional to the image diagonal
- point:   disc with a radius proportional to the image diagonal

Because all types become regions, a single point dropped inside a large
gold polygon gets a low IoU instead of counting as a full hit. Point-in-region
and normalized centroid distance are reported as secondary diagnostics only.

Geometry format (same as atlas / review files):
    {"type": "point"|"line"|"polygon", "coordinates": [[x, y], ...]}
in native image pixels, top-left origin. ``None`` means "not on this map"
(gold) or abstention (prediction).

Usage:
    python benchmark/eval_geometry.py --gold gold.jsonl --pred predictions.json \
        --out scores.json
Gold JSONL rows need event_id, geometry, width, height.
Use --from-review ANNOTATIONS REVIEWS to build gold from the review round
(latest accepted / modified_accepted decision per event).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

# Provisional parameters: freeze before the main model runs.
LINE_HALF_WIDTH_FRAC = 0.01   # line buffer half-width = 1% of image diagonal
POINT_RADIUS_FRAC = 0.02      # point disc radius = 2% of image diagonal
IOU_THRESHOLDS = (0.5, 0.75)
GEOMETRY_TYPES = ("point", "line", "polygon")


def _parse(value):
    """Accept dicts or the stringified dicts found in some review files."""
    if value is None or value == "None" or value == "":
        return None
    if isinstance(value, str):
        import ast
        value = ast.literal_eval(value)
    return value


def validate(geom):
    """Return a normalised geometry or raise ValueError."""
    geom = _parse(geom)
    if geom is None:
        return None
    gtype = geom.get("type")
    if gtype not in GEOMETRY_TYPES:
        raise ValueError(f"unknown geometry type: {gtype!r}")
    coords = geom.get("coordinates")
    if not isinstance(coords, list) or not coords:
        raise ValueError("coordinates must be a non-empty list")
    if gtype == "point" and isinstance(coords[0], (int, float)):
        raise ValueError("point must be [[x, y]], got [x, y]")
    pts = []
    for p in coords:
        if not (isinstance(p, (list, tuple)) and len(p) == 2):
            raise ValueError(f"bad vertex: {p!r}")
        x, y = float(p[0]), float(p[1])
        if not (math.isfinite(x) and math.isfinite(y)):
            raise ValueError("non-finite coordinate")
        pts.append((x, y))
    minimum = {"point": 1, "line": 2, "polygon": 3}[gtype]
    if len(pts) < minimum:
        raise ValueError(f"{gtype} needs at least {minimum} vertices")
    if gtype == "point" and len(pts) != 1:
        raise ValueError("point must have exactly one vertex")
    return {"type": gtype, "coordinates": pts}


def diagonal(width, height):
    return math.hypot(width, height)


def to_mask(geom, width, height, line_half_width_frac=LINE_HALF_WIDTH_FRAC,
            point_radius_frac=POINT_RADIUS_FRAC):
    """Rasterize a validated geometry into a boolean mask (height x width)."""
    img = Image.new("1", (width, height), 0)
    if geom is None:
        return np.zeros((height, width), dtype=bool)
    draw = ImageDraw.Draw(img)
    pts = geom["coordinates"]
    diag = diagonal(width, height)
    if geom["type"] == "polygon":
        draw.polygon(pts, fill=1, outline=1)
    elif geom["type"] == "line":
        r = max(1.0, line_half_width_frac * diag)
        draw.line(pts, fill=1, width=max(1, int(round(2 * r))))
        for x, y in pts:  # round joins and caps
            draw.ellipse([x - r, y - r, x + r, y + r], fill=1)
    else:
        r = max(1.0, point_radius_frac * diag)
        x, y = pts[0]
        draw.ellipse([x - r, y - r, x + r, y + r], fill=1)
    return np.array(img, dtype=bool)


def centroid(geom):
    xs = [p[0] for p in geom["coordinates"]]
    ys = [p[1] for p in geom["coordinates"]]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def score_event(gold, pred, width, height, pred_error=None, **params):
    """Score one event. ``gold``/``pred`` are raw geometries (or None).

    Returns a dict with outcome, iou, hits and diagnostics.
    outcome is one of: scored, correct_abstention, false_abstention,
    false_presence, invalid_prediction.
    """
    gold = validate(gold)
    out = {"gold_type": gold["type"] if gold else None, "pred_type": None,
           "iou": 0.0, "point_in_region": None, "centroid_dist_norm": None}
    if pred_error is not None:
        out.update(outcome="invalid_prediction", error=str(pred_error))
        return _hits(out)
    try:
        pred = validate(pred)
    except (ValueError, SyntaxError, TypeError) as exc:
        out.update(outcome="invalid_prediction", error=str(exc))
        return _hits(out)
    out["pred_type"] = pred["type"] if pred else None
    if gold is None:
        out["outcome"] = "correct_abstention" if pred is None else "false_presence"
        out["iou"] = 1.0 if pred is None else 0.0
        return _hits(out)
    if pred is None:
        out["outcome"] = "false_abstention"
        return _hits(out)
    g = to_mask(gold, width, height, **params)
    p = to_mask(pred, width, height, **params)
    union = np.logical_or(g, p).sum()
    out["iou"] = float(np.logical_and(g, p).sum() / union) if union else 0.0
    cx, cy = centroid(pred)
    ix, iy = int(round(cx)), int(round(cy))
    out["point_in_region"] = bool(0 <= ix < width and 0 <= iy < height and g[iy, ix])
    gx, gy = centroid(gold)
    out["centroid_dist_norm"] = math.hypot(cx - gx, cy - gy) / diagonal(width, height)
    out["type_match"] = pred["type"] == gold["type"]
    out["outcome"] = "scored"
    return _hits(out)


def _hits(out):
    for t in IOU_THRESHOLDS:
        out[f"hit@{t}"] = out["iou"] >= t
    return out


def aggregate(rows):
    """Summaries overall and per gold type. Every event counts; failures score 0."""
    groups = defaultdict(list)
    for r in rows:
        groups["all"].append(r)
        groups[r["gold_type"] or "outside_map"].append(r)
    summary = {}
    for name, items in groups.items():
        n = len(items)
        s = {"n": n,
             "mean_iou": sum(r["iou"] for r in items) / n,
             "outcomes": dict(sorted(_count(r["outcome"] for r in items).items()))}
        for t in IOU_THRESHOLDS:
            s[f"hit@{t}"] = sum(r[f"hit@{t}"] for r in items) / n
        scored = [r for r in items if r["outcome"] == "scored"]
        if scored:
            s["type_match_rate"] = sum(r["type_match"] for r in scored) / len(scored)
            s["point_in_region_rate"] = sum(r["point_in_region"] for r in scored) / len(scored)
            d = sorted(r["centroid_dist_norm"] for r in scored)
            s["median_centroid_dist_norm"] = d[len(d) // 2] if len(d) % 2 else (d[len(d) // 2 - 1] + d[len(d) // 2]) / 2
        summary[name] = s
    return summary


def _count(values):
    c = defaultdict(int)
    for v in values:
        c[v] += 1
    return c


# ---------------------------------------------------------------- loading

def load_gold_jsonl(path):
    gold = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            gold[row["event_id"]] = row
    return gold


def candidate_digest(record):
    return hashlib.sha256(json.dumps(record, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def load_review_gold(annotations_path, reviews_path,
                     accepted=("accepted", "modified_accepted", "accepted_no_location")):
    """Gold = latest review per event whose decision is accepted.

    Uses the reviewer's human_geometry when present, else the candidate geometry.
    "accepted_no_location" is a reviewer-confirmed abstention item: gold is None ("not on this map").
    A review whose candidate_sha256 no longer matches the candidate (text or geometry changed since) is stale and skipped,
    using the same digest as serve_reviews.py.
    """
    cands = {r["event_id"]: r for r in map(json.loads, _lines(annotations_path))}
    latest = {}
    for r in map(json.loads, _lines(reviews_path)):
        latest[r["event_id"]] = r
    gold = {}
    for eid, rev in latest.items():
        if rev.get("decision") not in accepted or eid not in cands:
            continue
        cand = cands[eid]
        if rev.get("candidate_sha256") and rev["candidate_sha256"] != candidate_digest(cand):
            continue
        image = _parse(rev.get("annotation_image") or cand.get("annotation_image"))
        geom = _parse(rev.get("human_geometry")) or _parse(cand.get("geometry"))
        if rev.get("decision") == "accepted_no_location" or (cand.get("status") == "outside_map" and not rev.get("human_geometry")):
            geom = None
        gold[eid] = {"event_id": eid, "geometry": geom,
                     "width": int(image["width"]), "height": int(image["height"])}
    return gold


def load_predictions(path):
    """Accept {"predictions": [...]}, a list, or JSONL. Rows: event_id, geometry, [error]."""
    text = Path(path).read_text(encoding="utf-8")
    try:
        data = json.loads(text)
        rows = data["predictions"] if isinstance(data, dict) else data
    except json.JSONDecodeError:
        rows = [json.loads(l) for l in text.splitlines() if l.strip()]
    return {r["event_id"]: r for r in rows}


def _lines(path):
    return [l for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]


def evaluate(gold, preds, **params):
    rows = []
    for eid in sorted(gold):
        g = gold[eid]
        p = preds.get(eid)
        if p is None:
            r = score_event(g["geometry"], None, g["width"], g["height"],
                            pred_error="missing prediction", **params)
        else:
            r = score_event(g["geometry"], p.get("geometry"), g["width"], g["height"],
                            pred_error=p.get("error"), **params)
        r["event_id"] = eid
        rows.append(r)
    return {"parameters": {"line_half_width_frac": params.get("line_half_width_frac", LINE_HALF_WIDTH_FRAC),
                           "point_radius_frac": params.get("point_radius_frac", POINT_RADIUS_FRAC),
                           "iou_thresholds": list(IOU_THRESHOLDS)},
            "summary": aggregate(rows), "events": rows,
            "unscored_predictions": sorted(set(preds) - set(gold))}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--gold", help="gold JSONL with event_id, geometry, width, height")
    src.add_argument("--from-review", nargs=2, metavar=("ANNOTATIONS", "REVIEWS"))
    ap.add_argument("--pred", required=True)
    ap.add_argument("--out")
    ap.add_argument("--line-half-width-frac", type=float, default=LINE_HALF_WIDTH_FRAC)
    ap.add_argument("--point-radius-frac", type=float, default=POINT_RADIUS_FRAC)
    a = ap.parse_args(argv)
    gold = load_gold_jsonl(a.gold) if a.gold else load_review_gold(*a.from_review)
    result = evaluate(gold, load_predictions(a.pred),
                      line_half_width_frac=a.line_half_width_frac,
                      point_radius_frac=a.point_radius_frac)
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
