#!/usr/bin/env python3
"""
visualise.py — Draw gold-coordinate marker on a benchmark map crop.

Usage:
  python3 benchmark/visualise.py E0001          # specific event
  python3 benchmark/visualise.py E0001 E0005    # multiple events
  python3 benchmark/visualise.py --random 5     # 5 random events
  python3 benchmark/visualise.py --all          # all 198 events

Output: benchmark/vis/{event_id}.jpg
"""

import argparse
import json
import random
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("pip install pillow")
    sys.exit(1)

BENCHMARK_PATH = Path("benchmark/place_benchmark_mixed_200_clean_v3.jsonl")
VIS_DIR        = Path("benchmark/vis")

MARKER_RADIUS  = 18     # outer circle radius (px)
INNER_RADIUS   = 5      # filled dot radius (px)
CROSSHAIR_LEN  = 30     # crosshair arm length (px)
COLOUR         = (220, 30, 30)          # red
SHADOW         = (255, 255, 255, 180)   # white semi-transparent shadow


def draw_marker(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    # Shadow pass (slightly offset, white)
    for dx, dy in [(-1, -1), (1, 1)]:
        draw.ellipse([x-MARKER_RADIUS+dx, y-MARKER_RADIUS+dy,
                      x+MARKER_RADIUS+dx, y+MARKER_RADIUS+dy],
                     outline=(255, 255, 255), width=3)
        draw.line([x-CROSSHAIR_LEN+dx, y+dy, x+CROSSHAIR_LEN+dx, y+dy],
                  fill=(255, 255, 255), width=3)
        draw.line([x+dx, y-CROSSHAIR_LEN+dy, x+dx, y+CROSSHAIR_LEN+dy],
                  fill=(255, 255, 255), width=3)

    # Marker
    draw.ellipse([x-MARKER_RADIUS, y-MARKER_RADIUS,
                  x+MARKER_RADIUS, y+MARKER_RADIUS],
                 outline=COLOUR, width=3)
    draw.ellipse([x-INNER_RADIUS, y-INNER_RADIUS,
                  x+INNER_RADIUS, y+INNER_RADIUS],
                 fill=COLOUR)
    draw.line([x-CROSSHAIR_LEN, y, x+CROSSHAIR_LEN, y], fill=COLOUR, width=2)
    draw.line([x, y-CROSSHAIR_LEN, x, y+CROSSHAIR_LEN], fill=COLOUR, width=2)


def add_caption(img: Image.Image, rec: dict) -> Image.Image:
    """Add a caption bar at the bottom with event info."""
    bar_h = 70
    out = Image.new("RGB", (img.width, img.height + bar_h), (30, 30, 30))
    out.paste(img, (0, 0))
    draw = ImageDraw.Draw(out)

    # Try system fonts, fall back to default
    font_lg = font_sm = ImageFont.load_default()
    for fname in ["/System/Library/Fonts/Helvetica.ttc",
                  "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        if Path(fname).exists():
            try:
                font_lg = ImageFont.truetype(fname, 15)
                font_sm = ImageFont.truetype(fname, 12)
            except Exception:
                pass
            break

    gx, gy = rec["gold_px"]
    line1 = f"{rec['event_id']}  |  {rec['place']}  ({rec['time']})  Tier {rec['tier']}"
    line2 = rec["event_text"][:110] + ("…" if len(rec["event_text"]) > 110 else "")
    line3 = f"gold_px = {gx}, {gy}  |  {rec['crop_km']:.0f} km crop  |  {rec['m_per_px']:.1f} m/px"

    draw.text((10, img.height + 4),  line1, fill=(255, 220, 80), font=font_lg)
    draw.text((10, img.height + 22), line2, fill=(200, 200, 200), font=font_sm)
    draw.text((10, img.height + 52), line3, fill=(150, 150, 150), font=font_sm)
    return out


def visualise(rec: dict, vis_dir: Path = VIS_DIR) -> Path:
    vis_dir.mkdir(parents=True, exist_ok=True)
    img  = Image.open(rec["image"]).convert("RGB")
    draw = ImageDraw.Draw(img)
    gx, gy = rec["gold_px"]
    draw_marker(draw, gx, gy)
    out_img = add_caption(img, rec)
    out_path = vis_dir / f"{rec['event_id']}.jpg"
    out_img.save(out_path, quality=92)
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*", help="Event IDs, e.g. E0001 E0005")
    ap.add_argument("--random", type=int, metavar="N", dest="rand",
                    help="Pick N random events")
    ap.add_argument("--all", action="store_true", help="Visualise all events")
    ap.add_argument("--benchmark", type=Path, default=BENCHMARK_PATH,
                    help="Benchmark JSONL path")
    ap.add_argument("--vis-dir", type=Path, default=VIS_DIR,
                    help="Output directory for visual QA images")
    args = ap.parse_args()

    records = {r["event_id"]: r
               for r in (json.loads(l) for l in open(args.benchmark, encoding="utf-8"))}

    if args.all:
        chosen = list(records.values())
    elif args.rand:
        chosen = random.sample(list(records.values()), min(args.rand, len(records)))
    elif args.ids:
        chosen = [records[i] for i in args.ids if i in records]
        missing = [i for i in args.ids if i not in records]
        if missing:
            print(f"Not found: {missing}")
    else:
        ap.print_help()
        return

    for rec in chosen:
        path = visualise(rec, args.vis_dir)
        print(f"  {rec['event_id']}  {rec['place'][:50]:50s}  → {path}")

    if len(chosen) == 1:
        import subprocess, sys
        if sys.platform == "darwin":
            subprocess.run(["open", str(path)])


if __name__ == "__main__":
    main()
