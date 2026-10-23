#!/usr/bin/env python3
"""Pixel geometry annotation. See benchmark/NAPOLEON_ANNOTATION.md."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import textwrap

import matplotlib.pyplot as plt
from matplotlib.widgets import Button, RadioButtons
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
FEATURE_TYPES = (
    ("bridge", "Bridge structure or its physical end"),
    ("ford", "Shallow river crossing / ford"),
    ("river_bank", "Land along the edge of a river"),
    ("river", "River channel or a section of water"),
    ("road", "Road, track or road segment"),
    ("junction", "Road junction or crossroads"),
    ("woodland", "Woods, forest or woodland edge"),
    ("high_ground", "Hill, ridge or slope"),
    ("open_ground", "Open field, meadow or plain"),
    ("settlement", "Village, town or built-up suburb"),
    ("building", "Individual building, mill or farm building"),
    ("other", "Unlisted or unspecified geographic feature"),
)


def prompt_feature_type(previous=None):
    codes = [code for code, _ in FEATURE_TYPES]
    default = previous if previous in codes else "other"
    print("Feature types (v1):")
    for number, (code, description) in enumerate(FEATURE_TYPES, start=1):
        print(f"  {number:2d}. {code:14s} {description}")
    if previous and previous not in codes:
        print(f"Previous type {previous!r} is outside this vocabulary; choose a current type.")
    while True:
        value = input(f"Feature number or code [{default}]: ").strip().lower()
        if not value:
            return default
        if value in codes:
            return value
        if value in {str(number) for number in range(1, len(codes) + 1)}:
            return codes[int(value) - 1]
        print(f"Choose 1-{len(codes)} or an exact code from the list.")


def load_jsonl(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def validate_geometry(kind, points, width, height):
    minimum = {"point": 1, "line": 2, "polygon": 3}[kind]
    if len(points) < minimum or (kind == "point" and len(points) != 1):
        raise ValueError(f"{kind} requires {'exactly' if kind == 'point' else 'at least'} {minimum} vertices")
    if len({tuple(p) for p in points}) != len(points):
        raise ValueError("Duplicate vertices")
    if any(not (0 <= x < width and 0 <= y < height) for x, y in points):
        raise ValueError("Vertex outside image")
    if kind == "polygon":
        from matplotlib.path import Path as MplPath
        edges = list(zip(points, points[1:] + points[:1]))
        for i, edge in enumerate(edges):
            for j in range(i + 1, len(edges)):
                if j == i + 1 or (i == 0 and j == len(edges) - 1):
                    continue
                if MplPath(edge).intersects_path(MplPath(edges[j]), filled=False):
                    raise ValueError("Polygon boundary crosses itself")
        area = abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in edges)) / 2
        if area < 1:
            raise ValueError("Polygon has no area")


def write_revision(path, ann):
    """Keep append-only revisions; latest record per ID is current."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(ann, ensure_ascii=False) + "\n")
        fh.flush()


def annotate_record(rec, previous, index, total):
    path = Path(rec["image"])
    if not path.is_absolute():
        path = ROOT / path
    with Image.open(path) as im:
        image = im.convert("RGB")
    width, height = image.size
    old_geometry = (previous or {}).get("geometry") or {}
    points = [list(p) for p in old_geometry.get("coordinates", [])]
    if not points and (previous or {}).get("geo_gold_px"):
        points = [previous["geo_gold_px"]]
    state = {"kind": old_geometry.get("type", "point"), "status": (previous or {}).get("status", "accepted"), "action": "quit"}
    fig = plt.figure(figsize=(14, 9))
    ax = fig.add_axes([.04, .12, .62, .80])
    ax.imshow(image)
    ax.set_xlim(-.5, width-.5)
    ax.set_ylim(height-.5, -.5)
    ax.set_title(f"{index}/{total}  {rec['event_id']}  {rec.get('place', '')}")
    line, = ax.plot([], [], "o-", color="crimson", markersize=4)
    status_text = fig.text(.04, .065, "", color="crimson")
    panel = fig.add_axes([.69, .45, .29, .48])
    panel.axis("off")
    body = "\n\n".join([rec.get("target_question", "Locate the event."), rec["event_text"],
                          "Source: " + rec.get("source_section", ""), rec.get("annotation_caution", "")])
    wrapped = "\n\n".join(textwrap.fill(p, 49) for p in body.split("\n\n"))
    text = panel.text(0, 1, wrapped, va="top", fontsize=10, clip_on=True)
    scroll = [0.0]

    def redraw():
        drawn = points + points[:1] if state["kind"] == "polygon" and len(points) > 2 else points
        line.set_data([p[0] for p in drawn], [p[1] for p in drawn])
        fig.canvas.draw_idle()

    kinds = ["point", "line", "polygon"]
    modes = RadioButtons(fig.add_axes([.69, .30, .13, .13]), kinds, active=kinds.index(state["kind"]))
    statuses = ["accepted", "ambiguous", "unlocatable", "rejected"]
    review = RadioButtons(fig.add_axes([.83, .28, .15, .16]), statuses, active=statuses.index(state["status"]))

    def mode(label):
        state["kind"] = label
        points.clear()
        redraw()

    modes.on_clicked(mode)
    review.on_clicked(lambda label: state.update(status=label))

    def click(event):
        if event.inaxes != ax or ax.get_navigate_mode():
            return
        if event.button == 3:
            if points:
                points.pop()
        elif event.button == 1 and event.xdata is not None:
            x, y = round(event.xdata), round(event.ydata)
            if not (0 <= x < width and 0 <= y < height):
                return
            if state["kind"] == "point":
                points.clear()
            points.append([x, y])
        redraw()

    def finish(action):
        if action == "save":
            try:
                if state["status"] == "accepted" or points:
                    validate_geometry(state["kind"], points, width, height)
            except ValueError as exc:
                status_text.set_text(str(exc))
                fig.canvas.draw_idle()
                return
        state["action"] = action
        plt.close(fig)

    buttons = []
    for label, x, action in [("Save", .69, "save"), ("Skip", .79, "skip"), ("Quit", .89, "quit")]:
        button = Button(fig.add_axes([x, .19, .085, .045]), label)
        button.on_clicked(lambda event, action=action: finish(action))
        buttons.append(button)

    def on_scroll(event):
        if event.inaxes == panel:
            scroll[0] = max(0, scroll[0] - event.step * .08)
            text.set_y(1 + scroll[0])
            fig.canvas.draw_idle()

    fig.canvas.mpl_connect("button_press_event", click)
    fig.canvas.mpl_connect("scroll_event", on_scroll)
    redraw()
    plt.show()
    if state["action"] != "save":
        return state["action"], None
    print("Previous evidence:", (previous or {}).get("evidence", ""))
    evidence = input("Evidence / reason (required; blank cancels save): ").strip()
    if not evidence:
        return "skip", None
    feature = prompt_feature_type((previous or {}).get("geo_feature_type"))
    tolerance = None
    if points and state["kind"] in ("point", "line"):
        while True:
            value = input("Tolerance in original-image pixels [0]: ").strip() or "0"
            try:
                tolerance = float(value)
                if not 0 <= tolerance <= max(width, height):
                    raise ValueError
                break
            except ValueError:
                print("Enter a finite non-negative pixel tolerance.")
    ann = {**rec, "schema_version": 2, "status": state["status"], "evidence": evidence,
           "gold_status": "human_annotated" if state["status"] == "accepted" else "not_accepted",
           "geometry": {"type": state["kind"], "coordinates": points} if points else None,
           "tolerance_px": tolerance, "geo_feature_type": feature,
           "geo_feature_vocab_version": 1,
           "geo_gold_px": points[0] if points and state["kind"] == "point" else None,
           "img_w": width, "img_h": height, "coordinate_system": "image_pixels_top_left",
           "updated_at": datetime.now(timezone.utc).isoformat()}
    return "save", ann


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "benchmark/map_first_candidates.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "benchmark/map_first_annotations.jsonl")
    parser.add_argument("--start", type=int, default=0, help="Index in original input (0-based)")
    parser.add_argument("--review", action="store_true", help="Reopen previously saved records")
    parser.add_argument("--annotator", default="anonymous")
    args = parser.parse_args()
    records = load_jsonl(args.input)
    if not records:
        parser.error("Input has no records")
    if args.input.resolve() == args.output.resolve():
        parser.error("Input and output must differ")
    previous = {r["event_id"]: r for r in load_jsonl(args.output)}
    for i, rec in enumerate(records):
        if i < args.start or (rec["event_id"] in previous and not args.review):
            continue
        print(f"\n{rec['event_id']} | {rec.get('article_url', '')}")
        print(rec.get("target_question", ""), rec["event_text"], sep="\n")
        try:
            action, ann = annotate_record(rec, previous.get(rec["event_id"]), i+1, len(records))
        except (FileNotFoundError, OSError) as exc:
            print(f"Cannot open map: {exc}")
            continue
        if action == "quit":
            break
        if ann:
            ann["annotator"] = args.annotator
            write_revision(args.output, ann)
            previous[rec["event_id"]] = ann
            print("Saved", rec["event_id"], ann["status"])


if __name__ == "__main__":
    main()
