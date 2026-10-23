# Zurich Ten Events: Normalized Qwen vs Historical GPT-6

Declared before inference, 2026-10-14 (Europe/Zurich).

- Run the original ten Zurich event questions, not ten independent maps.
- New model: cached official Qwen3-VL-8B-Instruct, revision
  `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b`, FP16, greedy decoding,
  seed 0, 4096 maximum new tokens. No quantization or new download.
- Use the unchanged clean input package from `zurich10_20260916_162847`.
  Preserve every original image pixel. Pad only right/bottom from
  1538 x 1754 to 1568 x 1760 and disable processor resizing.
- Replace only the event prompt's coordinate instruction with the previously
  tested explicit 0-1000 convention. Supply actual canvas width/height to the
  model; retain original passages, questions and geometry schema.
- Normalize to the whole supplied canvas: x_pixel=x/1000*1568 and
  y_pixel=y/1000*1760. Then strictly validate against the original content
  dimensions, rejecting padding positions. No clipping, shape repair,
  retrospective unit reinterpretation, retry or answer selection.
- Inference reads no human geometry or reference deployment map. Offline
  scoring uses the frozen human snapshot from the historical GPT-6 review.
- Reuse, never overwrite, GPT-6 Astra and native-pixel Qwen historical outputs.
  No new paid API call. Verify matching input package, tasks and image hashes.
- Preserve prior exclusions Z0009/Z0010 and outside-map test Z0003. Use
  provisional pixel diagnostics, not a ten-question overall accuracy.
- Report all ten outputs and failures. Compute mean/median point distance
  only for point-vs-point cases. Compare models on the same successful point
  IDs; report coverage, point-in-region and outside-map behavior separately.
- Historical Qwen used original image width/height in its prompt; this new
  request uses actual padded canvas dimensions. The coordinate instruction
  and declared dimensions both change. This is not a fresh, isolated
  coordinate-only causal ablation. Historical provider preprocessing and
  reasoning compute are not controlled; no claim of general model ranking.
- Persist original output, token IDs, prompt, pixel conversion, settings and
  checksums. Stop on backend errors, preserve partial attempts, and do not
  present incomplete inference as a completed comparison.
