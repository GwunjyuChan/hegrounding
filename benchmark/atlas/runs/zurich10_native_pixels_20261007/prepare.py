"""Freeze the old ten-question input and verify native-pixel preprocessing, without loading weights or gold."""
import io
import json
import os
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "benchmark"))
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

from PIL import Image
from transformers import AutoProcessor
from run_atlas_vlm import read_package, pad_image_without_resampling, digest

source = HERE.parent / "zurich10_20260916_162847/input.zip"
manifest, png, tasks, instruction = read_package(source)
assert [row["event_id"] for row in tasks] == [f"Z{i:04d}" for i in range(1, 11)]
assert not (HERE / "input.zip").exists()
image = Image.open(io.BytesIO(png)).convert("RGB")
model_path = Path.home() / ".cache/huggingface/hub/models--Qwen--Qwen3-VL-8B-Instruct/snapshots/0c351dd01ed87e9c1b53cbc748cba10e6187ff3b"
processor = AutoProcessor.from_pretrained(model_path, local_files_only=True)
padded, padding = pad_image_without_resampling(image, processor.image_processor.patch_size * processor.image_processor.merge_size)
inputs = processor.image_processor(images=[padded], do_resize=False, return_tensors="pt")
grid = inputs["image_grid_thw"].tolist()
assert grid == [[1, padded.height // 16, padded.width // 16]]
shutil.copy2(source, HERE / "input.zip")
(HERE / "map.png").write_bytes(png)
padded.save(HERE / "model_canvas.png")
(HERE / "prompt.txt").write_text(instruction)
for name in ("run_atlas_vlm.py", "test_native_pixels.py"):
    shutil.copy2(ROOT / "benchmark" / name, HERE / (name + ".snapshot"))
record = {"model": "Qwen/Qwen3-VL-8B-Instruct", "model_path": str(model_path),
          "source_input": str(source.relative_to(ROOT)), "input_zip_sha256": digest(source.read_bytes()),
          "map": manifest, "selected_event_ids": [t["event_id"] for t in tasks],
          "padding": padding, "image_grid_thw": grid,
          "processor_size": dict(processor.image_processor.size), "processor_do_resize": False,
          "prompt_and_questions_unchanged": True, "gold_not_loaded": True,
          "spatial_exclusions_declared_before_run": ["Z0009", "Z0010"],
          "outside_map_diagnostic": "Z0003", "max_output_tokens": 4096,
          "comparison": "Historical default-resize run vs new right/bottom-padding no-resize run; not a fresh paired baseline"}
(HERE / "manifest.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
print(json.dumps(record, ensure_ascii=False, indent=2))
