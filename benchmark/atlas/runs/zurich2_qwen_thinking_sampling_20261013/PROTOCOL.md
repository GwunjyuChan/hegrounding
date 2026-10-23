# Qwen3-VL Thinking: Recommended Sampling Pilot

Declared before inference on 2026-10-13. This is an exploratory two-case diagnostic, not a new ten-case model ranking.

## Fixed Inputs

- Cases chosen before sampled outputs: Z0003 (Regensdorf, outside the frozen map) and Z0004 (Altstetten, within-map point).
- Source: `benchmark/atlas/runs/zurich10_20260916_162847/input.zip`.
- Input ZIP SHA256: `c612c645322b5486d99dc9035e68a58ab9ca4aabc366ef8bf334f860419de11c`.
- Image SHA256: `fc5f835f11cd6f7cafefc7183b57d10c0911372149a1c2077f662a6d70570aec`.
- Keep the existing system prompt, questions and texts. No reference deployment map, human labels, or prior model answers enter inference.
- Preserve all 1538 x 1754 source pixels. Pad right/bottom to 1568 x 1760; disable image resizing. Verify the processed image grid.
- Do not change human annotations or any previous experiment outputs.

## Generation Configuration

Use the **VL** recommendation from the pinned [Qwen3-VL-8B-Thinking model card](https://huggingface.co/Qwen/Qwen3-VL-8B-Thinking/blob/92f3c4b4feadd3a016ef468d103bb5f58b2a2c6b/README.md):

- Checkpoint: `Qwen/Qwen3-VL-8B-Thinking`, revision `92f3c4b4feadd3a016ef468d103bb5f58b2a2c6b`.
- Official nonquantized weights, loaded as FP16 on Apple MPS, as in the previous experiment.
- `do_sample=true`, `temperature=1.0`, `top_p=0.95`, `top_k=20`, `repetition_penalty=1.0`.
- `presence_penalty=0.0`: no presence-penalty processor. Do not pass an unsupported generation argument to Transformers.
- `max_new_tokens=40960`, a ceiling rather than a required length. Allow the model's normal end-of-sequence token to stop generation early.
- Experimental seed: **0**, reset before each request. The seed is our reproducibility choice, not a model-card recommendation. One attempt per case; no best-of-N selection.
- These are the model-specific HF card parameters. Do not mix them with differently specified defaults from the evolving generic repository README.

## Checks And Interpretation

1. Record raw token IDs, prompt/template hashes, actual generation arguments, image preprocessing, elapsed time, and token counts.
2. Require a completed `</think>` block and parse only the final answer. Never extract draft coordinates from unfinished reasoning or repair malformed geometry.
3. Record whether the final answer finishes within 4096 or 8192 tokens, the previous greedy budgets. Record EOS versus budget exhaustion.
4. Compare output completion for these exact two cases against the existing greedy 4096/8192 runs. Include previous Instruct/GPT-6 outputs only as historical context; make no new API calls.
5. Assess outside-map abstention for Z0003. If Z0004 has a valid point, report distance to the unchanged provisional human point, explicitly not a validated accuracy score.
6. If the backend fails, retain the failed attempt and stop. Do not silently change precision, resolution, or sampling configuration.

Sampling and the maximum output budget both change relative to the previous run. A successful final answer would establish feasibility under this configuration, not prove a general accuracy improvement or isolate sampling as the sole cause. Two hand-selected diagnostic cases and one seed cannot establish a model ranking. Full evaluation requires a predeclared broader run and reviewed labels.

## Command

```sh
.venv/bin/python benchmark/run_qwen_thinking_eval.py \
  --mode thinking --generation-preset hf-thinking-vl --seed 0 \
  --event-id Z0003 --event-id Z0004 \
  --output benchmark/atlas/runs/zurich2_qwen_thinking_sampling_20261013/thinking \
  --execute
```

Outputs are isolated under this directory. The inference runner snapshots itself and the input ZIP before loading the model.
