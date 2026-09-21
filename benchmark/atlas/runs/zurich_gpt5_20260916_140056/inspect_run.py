"""Local diagnostic comparison only; never calls a model or changes gold."""
import argparse
import io
import json
import math
from pathlib import Path
import zipfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path as PolygonPath
import numpy as np
from PIL import Image, ImageDraw

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--run-dir", type=Path, default=Path(__file__).resolve().parent)
ROOT = parser.parse_args().run_dir
gold = json.loads((ROOT / "gold_snapshot.json").read_text())
run = json.loads((ROOT / "predictions.json").read_text())
assert run["map_version"] == gold["map"]["version"]
labels = {r["event_id"]: r for r in gold["annotations"]}
with zipfile.ZipFile(ROOT / "input.zip") as archive:
    background = Image.open(io.BytesIO(archive.read("map.png"))).convert("RGB")


def edge_distance(point, coords):
    p = np.array(point, dtype=float)
    distances = []
    for a, b in zip(coords, coords[1:] + coords[:1]):
        a, b = np.array(a, dtype=float), np.array(b, dtype=float)
        v = b - a
        t = np.clip(np.dot(p - a, v) / np.dot(v, v), 0, 1)
        distances.append(float(np.linalg.norm(p - a - t * v)))
    return min(distances)


def mask(geometry):
    im = Image.new("1", background.size)
    ImageDraw.Draw(im).polygon([tuple(p) for p in geometry["coordinates"]], fill=1)
    return np.asarray(im, dtype=bool)


def draw(ax, geometry, color, label):
    if geometry is None:
        return
    pts = np.array(geometry["coordinates"])
    if geometry["type"] == "point":
        ax.scatter(*pts[0], s=90, marker="x", color=color, linewidths=2.5, label=label)
    else:
        if geometry["type"] == "polygon":
            pts = np.vstack([pts, pts[0]])
        ax.plot(pts[:, 0], pts[:, 1], color=color, linewidth=2, label=label)


rows = []
for prediction in run["predictions"]:
    eid = prediction["event_id"]
    ann = labels[eid]
    assert ann["status"] == "accepted"
    g, p = ann["geometry"], prediction["geometry"]
    row = {"event_id": eid, "gold_type": g["type"],
           "prediction_type": p["type"] if p else None, "prediction": p}
    if p and g["type"] == p["type"] == "point":
        distance = math.dist(g["coordinates"][0], p["coordinates"][0])
        row.update(point_error_px=distance, tolerance_px=ann["tolerance_px"],
                   within_saved_tolerance=distance <= ann["tolerance_px"])
    elif p and g["type"] == "polygon" and p["type"] == "point":
        point, coords = p["coordinates"][0], g["coordinates"]
        distance = edge_distance(point, coords)
        inside = bool(PolygonPath(coords + coords[:1]).contains_point(point)) or distance < 1e-9
        row.update(point_inside_gold=inside, distance_to_gold_px=0.0 if inside else distance)
    elif p and g["type"] == p["type"] == "polygon":
        gm, pm = mask(g), mask(p)
        row["raster_iou_diagnostic"] = float(np.count_nonzero(gm & pm) / np.count_nonzero(gm | pm))
    rows.append(row)
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    for ax in axes:
        ax.imshow(background)
        draw(ax, g, "#dc303f", "Human gold")
        draw(ax, p, "#006bff", run["model"].rsplit("/", 1)[-1])
        ax.legend(loc="lower right")
        ax.set_xlabel("x (original pixels)")
        ax.set_ylabel("y (original pixels)")
    coords = g["coordinates"] + (p["coordinates"] if p else [])
    xs, ys = zip(*coords)
    axes[1].set_xlim(max(0, min(xs) - 60), min(background.width, max(xs) + 60))
    axes[1].set_ylim(min(background.height, max(ys) + 60), max(0, min(ys) - 60))
    axes[0].set_title(f"{eid}: full map")
    axes[1].set_title("Detail: red = human; blue = prediction")
    fig.tight_layout()
    fig.savefig(ROOT / f"{eid}_comparison.png", dpi=140)
    plt.close(fig)

attempts = [json.loads(s) for s in (ROOT / "predictions.attempts.jsonl").read_text().splitlines() if s]
usage = {k: sum((a.get("usage") or {}).get(k, 0) for a in attempts)
         for k in ("input_tokens", "output_tokens", "total_tokens")}
result = {"map_version": run["map_version"], "model": run["model"],
          "excluded": [r["event_id"] for r in gold["annotations"] if r["status"] != "accepted"],
          "metrics_kind": "diagnostic_against_saved_gold_not_formal_benchmark_accuracy",
          "rows": rows, "errors": run["errors"], "usage": usage}
(ROOT / "diagnostics.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(result, ensure_ascii=False, indent=2))
