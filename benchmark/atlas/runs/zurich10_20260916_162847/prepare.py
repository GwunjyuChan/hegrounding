"""Freeze this ten-candidate diagnostic run without changing research labels."""
import io
import json
from pathlib import Path
import sys
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "benchmark"))
from annotation_server import Store
from atlas_store import AtlasStore, digest
from run_atlas_vlm import read_package

atlas = AtlasStore(Store(ROOT))
mid = "074f543caf035b8f"
detail = atlas.detail(mid)
active = detail["active"]
assert active["version"] == "2ae3fca4eb15dced41f82401"
assert len(detail["events"]) == 10
assert all(e["gold"] for e in detail["events"])
paths = ("input.zip", "gold_snapshot.json", "review_snapshot.json", "integrity.json")
assert not any((HERE / p).exists() for p in paths), "Do not overwrite an existing run"

# Reuse the production prompt and image; explicitly include the outside-map
# control in this diagnostic package, without exposing its status to models.
with zipfile.ZipFile(io.BytesIO(atlas.export(mid, "input"))) as source:
    manifest = json.loads(source.read("manifest.json"))
    manifest["event_count"] = 10
    tasks = [{"event_id": e["id"], "map_version": active["version"],
              "image": "map.png", "width": active["width"], "height": active["height"],
              "text": e["text"], "question": e["question"]} for e in detail["events"]]
    with zipfile.ZipFile(HERE / "input.zip", "x", zipfile.ZIP_DEFLATED) as out:
        out.writestr("map.png", source.read("map.png"))
        out.writestr("prompt.txt", source.read("prompt.txt"))
        out.writestr("tasks.jsonl", "\n".join(json.dumps(t, ensure_ascii=False) for t in tasks) + "\n")
        out.writestr("manifest.json", json.dumps(manifest))
(HERE / "gold_snapshot.json").write_bytes(atlas.export(mid, "gold"))
review = {"scope": "ten_candidate_diagnostic_including_outside_map_control",
          "outside_map_control": ["Z0003"],
          "exclude_from_spatial_summary": {"Z0010": "Question asks for Korsakoff's city sector after redeployment; saved geometry/evidence describe Durasof and the retreat road. Preserve gold, require independent review."},
          "cautions": ["Saved point/line tolerances are zero; exact-match rates are not a meaningful historical localization threshold.",
                       "Z0009 asks for a road segment but saved gold is a point.",
                       "Map version, crop and gold differ from the preceding five-candidate runs; scores are not directly comparable.",
                       "All annotations and translations remain provisional; one shared map is not ten independent geographical samples."],
          "candidate_sha256": digest((ROOT / "benchmark/zurich_pilot_10.jsonl").read_bytes())}
(HERE / "review_snapshot.json").write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n")
integrity = {p: digest((ROOT / p).read_bytes()) for p in
             ("benchmark/atlas/gold.jsonl", "benchmark/atlas/maps.jsonl", "benchmark/zurich_pilot_10.jsonl")}
(HERE / "integrity.json").write_text(json.dumps(integrity, indent=2) + "\n")
print(read_package(HERE / "input.zip")[0])
print({e["id"]: e["gold"]["status"] for e in detail["events"]})
