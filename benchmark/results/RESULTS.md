# Benchmark Results — Place Grounding on Swiss Siegfried Maps

## 1. Benchmark Construction

### 1.1 Data Sources

**Events — HLS (Historical Dictionary of Switzerland)**
- Source: `hls-data-v2.json`, full local dump of ~36,000 HLS encyclopaedia articles
- Extraction script: `extraction/extract_place_events_from_hls_dump.py`
- Filtering criteria:
  - Article types: place / subject / event (people and families excluded)
  - Year range: 1292–1915 (must fall within the Swiss Siegfried map coverage period)
  - Keyword filter: events classified into three categories — war/conflict, transport, industrial
  - Geographic requirement: article must carry a native HLS coordinate (`article_geo`), used as the geocoding anchor

**Maps — Swisstopo Siegfried Map**
- Source: `https://wms.geo.admin.ch/`, layer `ch.swisstopo.hiks-siegfried`
- Crop: 6 km × 6 km centred on the event location, 1024 × 1024 px (~5.86 m/px)
- Fetch script: `maps/fetch_siegfried_crops.py`

**Geocoding — Swisstopo Geocoding API**
- Script: `maps/geocode_places.py`
- Converts HLS place names to LV95 coordinates, then to image pixel coordinates as the gold label
- All 200 items use `article_geo` (the HLS article's own coordinate), quality flag `auto_accept`

### 1.2 Benchmark Composition (v3 clean, n=200)

| Dimension | Distribution |
|-----------|-------------|
| Event type | war_conflict 100 / transport 50 / industrial 50 |
| Location type | All settlements |
| Year range | 1292–1915 |
| Tier | All Tier 1 (highest quality, auto-accepted geocoding) |
| Map crop | 6 km × 6 km, 1024×1024 px, ~5.86 m/px |
| Gold label source | HLS native coordinate (`article_geo`), all `auto_accept` |

Assembly script: `benchmark/assemble_place_benchmark.py`

---

## 2. Task Definition

**Input**: Historical Siegfried map image (1024×1024 px) + target place name

**Output**: VLM-predicted pixel coordinate `{x, y}` of the place on the map

**Gold label**: Swisstopo geocoded coordinate converted to image pixel coordinates

**Evaluation metrics**:
- `hit@500m` — predicted coordinate within 500 m of gold (primary metric)
- `hit@1000m` — within 1000 m of gold
- `beyond_1000m` — more than 1000 m from gold
- `median` / `mean` — prediction error distance in metres

**Visualisation**: red circle = 500 m radius, orange circle = 1000 m radius, blue crosshair = model prediction

---

## 3. Models

| Provider | Model ID | Type | Inference |
|----------|----------|------|-----------|
| Qwen3-VL-8B | `Qwen/Qwen3-VL-8B-Instruct` | Open-source VLM | Local MPS (Apple Silicon, float16) |
| GPT-4o | `gpt-4o` | Closed-source | OpenAI Responses API |
| GPT-5 | `gpt-5` | Closed-source (reasoning) | OpenAI Responses API, `reasoning_effort=minimal` |

Prompt structure: `SYSTEM_PROMPT` + map size/extent description + target place name + requirement to output `{"x": int, "y": int, "confidence": float}`

---

## 4. Main Results

### 4.1 Full Benchmark (n=200)

| Model | hit@500m | hit@1000m | beyond_1000m | median | mean |
|-------|---------|---------|------------|--------|------|
| **Qwen3-VL-8B** | **60.0%** | **93.0%** | 7.0% | **431 m** | **536 m** |
| GPT-5 | 23.5% | 72.0% | 28.0% | 784 m | 808 m |

Result files: `qwen3vl_8b_place_200.jsonl`, `gpt5_place_200.jsonl`

### 4.2 Cross-validation — Same Samples (n=20, seed=42)

| Model | hit@500m | hit@1000m | beyond_1000m | median |
|-------|---------|---------|------------|--------|
| **Qwen3-VL-8B** | **55.0%** | **95.0%** | 5.0% | 477 m |
| GPT-4o | 25.0% | 75.0% | 25.0% | 880 m |
| GPT-5 | 15.0% | 65.0% | 35.0% | 853 m |

Result files: `qwen3vl_8b_place_20_seed42.jsonl`, `gpt4o_place_20_seed42.jsonl`, `gpt5_place_20_seed42.jsonl`

### 4.3 Breakdown by Event Type (n=200)

| Event type | n | Qwen hit@500m | GPT-5 hit@500m | Qwen median |
|-----------|---|-------------|--------------|------------|
| transport | 50 | **68.0%** | 26.0% | 347 m |
| industrial | 50 | 58.0% | 24.0% | 468 m |
| war_conflict | 100 | 57.0% | 22.0% | 454 m |

---

## 5. Key Findings

1. **Qwen3-VL-8B outperforms closed-source models across the board**: hit@500m is 2.5× that of GPT-5 (60% vs 23.5%), consistent across all event types.

2. **Small-sample conclusions hold**: 20-sample results (55%) align with 200-sample results (60%), confirming that the seed-42 cross-validation subset is representative.

3. **GPT-5 is poorly suited to coordinate localisation**: with `reasoning_effort=minimal`, reasoning_tokens are uniformly 0; on the 20-sample cross-validation GPT-5 underperforms even GPT-4o (15% vs 25%). Reasoning mode provides limited benefit for direct visual localisation tasks.

4. **Transport events are easiest to localise** (Qwen 68% hit@500m), likely because transport infrastructure (stations, bridges) appears with clear legend symbols on Siegfried maps.

5. **Qwen3-VL-8B runs fully locally**: MacBook Pro 48 GB unified memory (Apple Silicon MPS, float16), ~10 s/item inference, zero API cost. First run requires downloading ~16 GB of model weights from HuggingFace.

6. **Representative failure case**: M0062 Unspunnen consistently outputs `{"x": 123, "y": 456}` (placeholder values), indicating the model has no confidence on certain historical place names and falls back to a fixed response.

---

## 6. Experiment Log

| Date | Run ID | Model | n | Seed | Notes |
|------|--------|-------|---|------|-------|
| 2026-08-25 | `qwen3vl_8b_place_20_seed42` | Qwen3-VL-8B | 20 | 42 | Three-model cross-validation |
| 2026-08-25 | `gpt4o_place_20_seed42` | GPT-4o | 20 | 42 | Three-model cross-validation |
| 2026-08-25 | `gpt5_place_20_seed42` | GPT-5 | 20 | 42 | Three-model cross-validation |
| 2026-08-25 | `qwen3vl_8b_place_200` | Qwen3-VL-8B | 200 | 13 | Full benchmark |
| 2026-08-25 | `gpt5_place_200` | GPT-5 | 200 | 13 | Full benchmark |

---

## 7. Pending

- [ ] Event task (give event text description rather than place name; test VLM event understanding + localisation)
- [ ] GPT-4o full 200-item comparison
- [ ] Fine-grained events (street/building level) — annotation and evaluation
- [ ] CLIP embedding index for metadata-free map matching
