"""Offline explanatory figures and supplementary diagnostics, never changing primary scores."""
import io
import json
import math
from pathlib import Path
import statistics
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "benchmark"))
from PIL import Image, ImageDraw, ImageFont
from compare_grounding_methods import point_distance
from run_atlas_vlm import read_package

FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
COLORS = {"qwen_native": "#087849", "gpt5": "#874bb1", "gpt6_astra": "#066ed4"}
NAMES = {"qwen_native": "Qwen3-VL (native)", "gpt5": "GPT-5", "gpt6_astra": "GPT-6 Astra"}


def text(draw, xy, value, size=20, color="#20272d"):
    draw.text(xy, value, font=ImageFont.truetype(FONT, size), fill=color)


def overlay(draw, geometry, origin, color, gold=False):
    if not geometry:
        return
    ox, oy = origin
    coords = [(x-ox, y-oy+104) for x, y in geometry["coordinates"]]
    if geometry["type"] == "point":
        x, y = coords[0]
        if gold:
            draw.line([(x-11,y),(x+11,y)], fill=color, width=4)
            draw.line([(x,y-11),(x,y+11)], fill=color, width=4)
        else:
            draw.ellipse((x-8,y-8,x+8,y+8), outline="white", width=5)
            draw.ellipse((x-7,y-7,x+7,y+7), outline=color, width=3)
    else:
        draw.line(coords + coords[:1] if geometry["type"] == "polygon" else coords,
                  fill="white", width=6, joint="curve")
        draw.line(coords + coords[:1] if geometry["type"] == "polygon" else coords,
                  fill=color, width=3, joint="curve")


def main():
    report = json.loads((HERE / "review/diagnostics.json").read_text())
    gold = json.loads((HERE / "review/gold_snapshot.json").read_text())
    labels = {a["event_id"]: a for a in gold["annotations"]}
    _, png, tasks, _ = read_package(HERE / "input.zip")
    background = Image.open(io.BytesIO(png)).convert("RGB")
    out = HERE / "review/report_figures"
    out.mkdir(exist_ok=True)
    rows = report["rows"]
    titles = {"Z0002": "Closter-Fahr: Russian battalions", "Z0004": "Altstetten: Klein before departure",
              "Z0006": "Dietikon: troops before embarkation", "Z0007": "Wollishofen: approach locality",
              "Z0008": "Hong: captured camp locality", "Z0005": "Heights: point gold vs predicted area",
              "Z0009": "Road question: point gold (NOT SCORED)", "Z0010": "City-side question: road gold (NOT SCORED)"}
    crops = {}
    for eid, title in titles.items():
        points = list(labels[eid]["geometry"]["coordinates"])
        for method in COLORS:
            geometry = rows[method][eid]["geometry"]
            points += geometry["coordinates"] if geometry else []
        x0, y0 = max(0, math.floor(min(p[0] for p in points))-80), max(0, math.floor(min(p[1] for p in points))-80)
        x1, y1 = min(background.width, math.ceil(max(p[0] for p in points))+80), min(background.height, math.ceil(max(p[1] for p in points))+80)
        width, height = max(760, x1-x0), max(320, y1-y0)
        x0 = max(0, min(background.width-width, (x0+x1-width)//2))
        y0 = max(0, min(background.height-height, (y0+y1-height)//2))
        x1, y1 = x0+width, y0+height
        crop = background.crop((x0,y0,x1,y1))
        width = max(760, crop.width)
        im = Image.new("RGB", (width, crop.height+170), "white")
        im.paste(crop,(0,104))
        draw = ImageDraw.Draw(im)
        text(draw,(16,10),f"{eid} | {title}",24)
        text(draw,(16,44),"Human GT",18,"#d42846")
        for i, method in enumerate(COLORS):
            text(draw,(150+i*200,44),NAMES[method],18,COLORS[method])
        text(draw,(16,74),f"Original pixels | crop x=[{x0},{x1}), y=[{y0},{y1})",16)
        overlay(draw,labels[eid]["geometry"],(x0,y0),"#d42846",gold=True)
        for method in COLORS:
            overlay(draw,rows[method][eid]["geometry"],(x0,y0),COLORS[method])
        caption = "Cross: human point; circles: model points; outlines: lines / polygons."
        text(draw,(16,im.height-54),caption,17)
        text(draw,(16,im.height-28),"No image resampling. Invalid output is not drawn. Provisional human labels.",16)
        im.save(out/f"{eid}_detail.png")
        crops[eid] = [x0,y0,x1,y1]

    ids = ["Z0002","Z0004","Z0006"]
    chart = Image.new("RGB", (1100,540), "white")
    draw = ImageDraw.Draw(chart)
    text(draw,(28,20),"Point error on identical questions",28)
    text(draw,(28,60),"Pixels; lower is better. Missing/invalid output is not zero error.",20)
    for i,m in enumerate(COLORS):
        text(draw,(28+i*325,98),NAMES[m],20,COLORS[m])
    for i,eid in enumerate(ids):
        y = 158+i*108
        text(draw,(28,y+20),eid,22)
        for j,m in enumerate(COLORS):
            yy=y+j*27
            value=rows[m][eid].get("distance_to_gold_px")
            if value is None:
                text(draw,(165,yy),"No valid output",18,COLORS[m])
            else:
                end=165+value*.95
                draw.rectangle((165,yy+3,end,yy+19),fill=COLORS[m])
                text(draw,(end+10,yy),f"{value:.1f}",18,COLORS[m])
    text(draw,(28,505),"GPT-5 / all-three common subset: Z0004 and Z0006 only.",18)
    chart.save(out/"point_errors.png")

    directories={"qwen_native":HERE.parent/"zurich10_native_pixels_20261007",
                 "gpt5":HERE.parent/"zurich10_20260916_162847/gpt5", "gpt6_astra":HERE}
    supplementary={"figure_crops":crops,"unique_passages":len({t["text"] for t in tasks}),
                   "image_diagonal_px":math.hypot(*background.size),"timing":{},"all_three_common_points":{},
                   "within_map_gold_coverage":{}}
    for m,directory in directories.items():
        attempts=[json.loads(s) for s in (directory/"predictions.attempts.jsonl").read_text().splitlines()]
        durations=[a["elapsed_seconds"] for a in attempts]
        supplementary["timing"][m]={"median_seconds":statistics.median(durations),"total_seconds":sum(durations),
            "reasoning_tokens":sum((a.get("usage") or {}).get("output_tokens_details",{}).get("reasoning_tokens",0) for a in attempts) if m!="qwen_native" else None}
        values=[rows[m][eid]["distance_to_gold_px"] for eid in ("Z0004","Z0006")]
        supplementary["all_three_common_points"][m]={"event_ids":["Z0004","Z0006"],"mean_px":statistics.mean(values)}
        supplementary["within_map_gold_coverage"][m]={"point_distance_n":sum("distance_to_gold_px" in rows[m][eid] for eid in ("Z0001","Z0002","Z0004","Z0005","Z0006")),"point_gold_n":5,"region_point_n":2}
    raw=json.loads((HERE/"predictions.attempts.jsonl").read_text().splitlines()[0])["raw"]
    raw_point=json.loads(raw)["geometry"]["coordinates"]
    supplementary["exploratory_Z0001"]={"not_a_valid_prediction":True,"raw_coordinates":raw_point,
        "distance_if_shape_normalized_px":math.dist(raw_point,labels["Z0001"]["geometry"]["coordinates"][0])}
    supplementary["exploratory_Z0005"]={"not_primary_score":True,
        "gold_point_to_predicted_polygon_px":point_distance(labels["Z0005"]["geometry"]["coordinates"][0],rows["gpt6_astra"]["Z0005"]["geometry"])}
    (out/"supplementary.json").write_text(json.dumps(supplementary,indent=2)+"\n")
    print(json.dumps(supplementary,indent=2))


if __name__ == "__main__":
    main()
