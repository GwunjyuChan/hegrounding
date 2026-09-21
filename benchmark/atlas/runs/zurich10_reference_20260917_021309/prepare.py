"""Reference-map input ablation, isolated from the live annotation workspace."""
import io
import json
from pathlib import Path
import shutil
import sys
import zipfile

from PIL import Image, ImageChops

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "benchmark"))
from annotation_server import Store
from atlas_store import AtlasStore, digest
from run_atlas_vlm import read_package

source_zip = ROOT / "benchmark/atlas/runs/zurich10_20260916_162847/input.zip"
old_manifest, _, old_tasks, prompt = read_package(source_zip)
workspace = HERE / "reference_workspace"
workspace.mkdir(exist_ok=False)
reference = Path("maps/zurich_pilot/zurich2.jpg")
(workspace / reference).parent.mkdir(parents=True)
shutil.copyfile(ROOT / reference, workspace / reference)
(workspace / "benchmark").mkdir()
shutil.copyfile(ROOT / "benchmark/zurich_pilot_10.jsonl", workspace / "benchmark/zurich_pilot_10.jsonl")
atlas = AtlasStore(Store(workspace))
mid = digest(str(reference).encode())[:16]
source = atlas.import_source((workspace / reference).read_bytes(), reference.name)
detail = atlas.save_map(mid, {"base_revision": None, "source_id": source["id"],
    "crop": [0, 0, source["width"], source["height"]], "rotation": 0, "max_side": 3200,
    "title": "苏黎世作战参考图输入实验 · 含部署提示 · 独立审核",
    "provenance": "Napoleon Series zurich2.jpg. Full reference battle map, with original troop symbols and arrows. Diagnostic input ablation with answer cues; not an answer-free benchmark. No gold labels transferred from the Usteri 1816 map."})
active = detail["active"]
png = atlas.asset_path(active["version"]).read_bytes()
with Image.open(ROOT / reference) as original, Image.open(io.BytesIO(png)) as converted:
    assert original.size == converted.size == (2177, 1699)
    assert ImageChops.difference(original.convert("RGB"), converted.convert("RGB")).getbbox() is None
tasks = [{**t, "width": active["width"], "height": active["height"], "map_version": active["version"]} for t in old_tasks]
for before, after in zip(old_tasks, tasks):
    assert {k: before[k] for k in ("event_id", "text", "question")} == {k: after[k] for k in ("event_id", "text", "question")}
manifest = {"map_version": active["version"], "image_sha256": active["image_sha256"],
    "coordinate_system": "image_pixels_top_left", "event_count": len(tasks),
    "input_condition": "reference_battle_map_with_deployment_and_arrow_cues",
    "answer_cue_leakage": True, "independent_reference_gold_available": False,
    "baseline_input_sha256": digest(source_zip.read_bytes()),
    "reference_original_sha256": digest((ROOT / reference).read_bytes())}
with zipfile.ZipFile(HERE / "input.zip", "x", zipfile.ZIP_DEFLATED) as archive:
    archive.writestr("map.png", png)
    archive.writestr("prompt.txt", prompt)
    archive.writestr("tasks.jsonl", "\n".join(json.dumps(t, ensure_ascii=False) for t in tasks) + "\n")
    archive.writestr("manifest.json", json.dumps(manifest))
(HERE / "experiment.json").write_text(json.dumps({"reference_map": active,
    "baseline_map": old_manifest, "method": "Qwen3-VL direct grounding; only map and its coordinate metadata replaced",
    "known_confounds": ["different geographic coverage", "different resolution, scale and cartography", "visible military answer cues"],
    "scoring": "No cross-map pixel scoring; human reference-map annotation required",
    "main_workspace_unchanged": {p: digest((ROOT / p).read_bytes()) for p in
       ("benchmark/atlas/gold.jsonl", "benchmark/atlas/maps.jsonl", "benchmark/atlas/predictions.jsonl")}}, ensure_ascii=False, indent=2) + "\n")
assert len(read_package(HERE / "input.zip")[2]) == 10
print(json.dumps(manifest, indent=2))
print("Independent review workspace:", workspace)
