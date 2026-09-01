# Minimal VLM Eval Pipeline

This pipeline evaluates place-level grounding on the mixed 200-item benchmark.

Default benchmark:

```bash
benchmark/place_benchmark_mixed_200_local.jsonl
```

## 1. Smoke Tests Without API Calls

Centre baseline:

```bash
python3 benchmark/vlm_eval.py \
  --provider center \
  --task place \
  --limit 20 \
  --run-name center_place_20 \
  --no-resume
```

Oracle plumbing test:

```bash
python3 benchmark/vlm_eval.py \
  --provider oracle \
  --task place \
  --limit 20 \
  --run-name oracle_place_20 \
  --no-resume
```

## 2. Place-Name Grounding

This is the first real VLM test. The prompt gives the model only the target place
name and the historical map crop.

The script loads `.env` from the project root by default. Both forms are accepted:

```bash
OPENAI_API_KEY=...
export OPENAI_API_KEY=...
```

```bash
export OPENAI_API_KEY=...

python3 benchmark/vlm_eval.py \
  --provider openai \
  --model gpt-4o \
  --task place \
  --sample 20 \
  --run-name openai_place_20
```

## 3. Event-Text Grounding

This gives the model the event description instead of the explicit target-place
field.

```bash
python3 benchmark/vlm_eval.py \
  --provider openai \
  --model gpt-4o \
  --task event \
  --sample 20 \
  --run-name openai_event_20
```

## 4. Open-Source / Local VLMs

For open-source models, run the model behind an OpenAI-compatible
`/v1/chat/completions` server, then use `--provider openai-chat`.

Example:

```bash
python3 benchmark/vlm_eval.py \
  --provider openai-chat \
  --base-url http://localhost:8000/v1 \
  --model <your-vision-model-name> \
  --task place \
  --sample 20 \
  --run-name local_place_20
```

Notes:

- the model must support image input;
- many local servers require an API key value even if they ignore it, so set a
  dummy key if needed: `export OPENAI_API_KEY=EMPTY`;
- use `--task place` first, then compare with `--task event`.

## 5. Outputs

Result JSONL:

```bash
benchmark/results/<run-name>.jsonl
```

Prediction visualisations:

```bash
benchmark/pred_vis/<run-name>/<event-id>.jpg
```

Visualisation colours:

- red = gold HLS place coordinate
- blue = model prediction

## 6. Recommended Order

1. Run `center` on all 200 items.
2. Run `place` with a VLM on 20 random items.
3. Inspect prediction visualisations.
4. If parsing and outputs look good, run `place` on all 200.
5. Run `event` on the same split and compare against `place`.
6. Add random-offset crops if the centre baseline is too strong.
