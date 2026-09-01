# HE-Grounding — Historical Event Grounding on Swiss Siegfried Maps

VLM benchmark for localising historical events on historical Swiss map images.

## Project Structure

```
hegrounding/
├── benchmark/                              # Evaluation pipeline
│   ├── vlm_eval.py                         # Main eval script (all providers)
│   ├── assemble_place_benchmark.py         # Benchmark assembly
│   ├── place_benchmark_2_5km_20_seed42.jsonl  # Active benchmark (2.5 km crop)
│   ├── results/                            # Experiment result JSONL files
│   │   └── RESULTS.md                      # Results summary & comparison table
│   └── pred_vis/                           # Per-item visualisations (gitignored)
├── data/                                   # Large source files (gitignored, see Data Setup)
├── docs/                                   # Showcase and figures
│   └── SHOWCASE.md                         # Annotated prediction examples
├── extraction/                             # Event extraction from HLS
├── maps/                                   # Geocoding & Siegfried map fetching
├── archive/                                # Legacy benchmark versions & 6 km results
├── pyproject.toml                          # Dependencies (uv)
└── uv.lock                                 # Pinned dependency versions
```

## Quick Start

```bash
# Install dependencies
uv sync

# Run evaluation — place task
uv run python benchmark/vlm_eval.py \
  --benchmark benchmark/place_benchmark_2_5km_20_seed42.jsonl \
  --provider qwen \
  --model Qwen/Qwen3-VL-8B-Instruct \
  --task place

# Providers: center | oracle | openai | openai-chat | anthropic | qwen
```

## Key Results (place task, 2.5 km crop, n=20, seed=42)

| Model | hit@250m | hit@500m | hit@1000m | median |
|-------|---------|---------|---------|--------|
| **Qwen3-VL-8B** (local) | **25.0%** | **65.0%** | **100.0%** | 475 m |

→ Full results: [`benchmark/results/RESULTS.md`](benchmark/results/RESULTS.md)  
→ Prediction showcase: [`docs/SHOWCASE.md`](docs/SHOWCASE.md)

## Data Setup

Large source data files are not tracked in git. Place them in `data/` before running extraction scripts:

| File | Description | Size |
|------|-------------|------|
| `data/hls-data-v2.json` | HLS full article dump (~36,000 articles) | ~141 MB |

The extraction script `extraction/extract_place_events_from_hls_dump.py` reads from `data/hls-data-v2.json` by default.

## Dependencies

Managed via [uv](https://docs.astral.sh/uv/). All dependencies are declared in `pyproject.toml` and pinned in `uv.lock`.

- `transformers >= 4.51` + `torch >= 2.3` + `torchvision` — Qwen3-VL local inference
- `openai >= 2.53` — GPT-4o / GPT-5 via API
- `qwen-vl-utils`, `accelerate`, `pillow`
