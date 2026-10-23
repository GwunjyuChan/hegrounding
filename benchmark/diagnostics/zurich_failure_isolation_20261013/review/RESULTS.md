# Zurich Failure-Isolation Results

Exploratory local Qwen3-VL-8B Thinking and Instruct diagnostics, 2026-10-13.

Historical label boxes are assistant-provisional, not verified human gold. Text-center tasks and event-location tasks are scored separately. No old annotations or results were modified.

## Main Conclusion

The tested coordinate-output convention is a substantial source of error, not just historical-map readability. Fresh Instruct calls using explicit 0-1000 coordinates land inside the Altstetten reference text box on both the synthetic and historical images; pixel-output calls do not. Thinking also improves on the historical-label control, but still misses the reference box. This diagnoses coordinate-instruction compliance as part of the problem, not a universal fix for event grounding.

![Full-map predictions shown in a readable display-only crop](coordinate_comparison.png)

The green boxes were frozen before these calls but remain assistant-provisional. Crops above are for review only: no crop or reference marker was sent to the model. Row-to-row comparisons also change decoding and chat templates, so this is not a clean Thinking-vs-Instruct ranking.

## Execution

Valid final outputs: **15/20 completed calls**. Text answers matching the target place: **2/2**. Recorded-call inference: **53.5 min** (excludes the interrupted call and setup). Tokens: **37477**.

The original 16-call multi-target plan stopped after four complete attempts, during its fifth call. Both multi-target synthetic controls had exhausted 4096 tokens. A declared adaptive follow-up switched to one requested label, retaining the schema, image, settings and budget. Follow-up calls completed: **12/12**; stop reason: **all completed**. Cancelled/unattempted calls are not model failures or zero-error predictions.

Thinking calls share the FP16 checkpoint, official sampling parameters, per-request seed and 4096-token diagnostic budget. Four additional Instruct positive controls use the same image/user/system content with greedy decoding and its own non-thinking chat template. This control is not an isolated checkpoint-only ablation or a model ranking. Input images are verified unscaled, with actual visual-token counts checked. Coordinate modes use the supplied canvas dimensions. Truncated output is not a wrong spatial prediction.

## Text Only

| Event | Target | Answer | Exact match |
|---|---|---|---|
| Z0003 | Regensdorf | Regensdorf | True |
| Z0004 | Altstetten | Altstetten | True |

## Diagnostic Findings

- Text extraction: 2/2 exact target-place answers. These two questions do not show a text-extraction failure.
- Completion instability occurs even on the synthetic clear-text image. A truncated answer supplies no location-error measurement and cannot prove a visual failure.
- Thinking, same full-map Altstetten label: pixel-prompt center error 370.5 px; relative-coordinate prompt 139.9 px. This is one label/seed, not a benchmark accuracy change.
- Instruct control, same full-map Altstetten label: pixel-prompt center error 346.5 px; relative-coordinate prompt 32.0 px. This is one label/seed, not a benchmark accuracy change.
- Thinking, fixed tiles: 1 false-presence predictions among 3 completed absent-label tile queries. Whole-map reconstruction is ambiguous; no oracle selects a candidate.
- The recorded image hashes, nonzero visual-token counts, finite input tensors and unscaled dimensions rule out the specific missing-image/downsampling failures checked here. They do not rule out every internal backend, precision or model issue.
- These are adaptive exploratory diagnostics. Any remaining model-internal cause is unresolved; do not infer an intrinsic Thinking-vs-Instruct ranking from different decoding/template conditions.


## Label-Center Diagnostics

Center error is to the center of the reference text box; box error is distance to its boundary (zero inside). A missing final output is not scored as zero error.

| Call | Altstetten | ZURICH | Regensdorf |
|---|---|---|---|
| [labels_synthetic_pixels_s0](overlays/labels_synthetic_pixels_s0.png) | IncompleteThinking | IncompleteThinking | IncompleteThinking |
| [labels_synthetic_normalized_1000_s0](overlays/labels_synthetic_normalized_1000_s0.png) | IncompleteThinking | IncompleteThinking | IncompleteThinking |
| [single_labels_synthetic_normalized_1000_s0](overlays/single_labels_synthetic_normalized_1000_s0.png) | IncompleteThinking | not requested | not requested |
| [single_labels_synthetic_pixels_s0](overlays/single_labels_synthetic_pixels_s0.png) | 184.7 px center; 128.1 px box | not requested | not requested |
| [single_labels_full_normalized_1000_s0](overlays/single_labels_full_normalized_1000_s0.png) | 139.9 px center; 85.6 px box | not requested | not requested |
| [single_labels_full_pixels_s0](overlays/single_labels_full_pixels_s0.png) | 370.5 px center; 309.8 px box | not requested | not requested |
| [single_labels_tile_TL](overlays/single_labels_tile_TL.png) | correct absent | not requested | not requested |
| [single_labels_tile_TR](overlays/single_labels_tile_TR.png) | 88.0 px center; 67.8 px box | not requested | not requested |
| [single_labels_tile_BL](overlays/single_labels_tile_BL.png) | correct absent | not requested | not requested |
| [single_labels_tile_BR](overlays/single_labels_tile_BR.png) | FALSE PRESENT | not requested | not requested |
| [instruct_labels_synthetic_normalized_1000_s0](overlays/instruct_labels_synthetic_normalized_1000_s0.png) | 19.0 px center; 0.0 px box | not requested | not requested |
| [instruct_labels_synthetic_pixels_s0](overlays/instruct_labels_synthetic_pixels_s0.png) | 161.6 px center; 120.1 px box | not requested | not requested |
| [instruct_labels_full_normalized_1000_s0](overlays/instruct_labels_full_normalized_1000_s0.png) | 32.0 px center; 0.0 px box | not requested | not requested |
| [instruct_labels_full_pixels_s0](overlays/instruct_labels_full_pixels_s0.png) | 346.5 px center; 285.7 px box | not requested | not requested |

## Full-Image Coordinate Comparison

| Group | Mode | Points / visible queries | In text box | Mean center error (px) | Correct absent / absent queries |
|---|---|---:|---:|---:|---:|
| multi_synthetic | pixels | 0/3 | 0 | N/A | 0/0 |
| multi_synthetic | normalized_1000 | 0/3 | 0 | N/A | 0/0 |
| single_synthetic | pixels | 1/1 | 0 | 184.7 | 0/0 |
| single_synthetic | normalized_1000 | 0/1 | 0 | N/A | 0/0 |
| single_full | pixels | 1/1 | 0 | 370.5 | 0/0 |
| single_full | normalized_1000 | 1/1 | 0 | 139.9 | 0/0 |
| instruct_synthetic | pixels | 1/1 | 0 | 161.6 | 0/0 |
| instruct_synthetic | normalized_1000 | 1/1 | 1 | 19.0 | 0/0 |
| instruct_full | pixels | 1/1 | 0 | 346.5 | 0/0 |
| instruct_full | normalized_1000 | 1/1 | 1 | 32.0 | 0/0 |

The completed follow-up uses one seed and one requested label per call. The originally planned two-seed full-map batch comparison was not completed. Means exclude missing/abstained points, so read coverage alongside errors. Do not combine these tasks into one accuracy.

## Fixed-Tile Reconstruction

All four tiles are required. Exactly one non-null candidate is required to reconstruct a map-level point. Multiple candidates remain ambiguous; missing/failed tiles yield incomplete. No gold-selected best tile.

| Name | Status | Candidates (full-image pixels) |
|---|---|---|
| Altstetten | ambiguous | TR: (876.8, 179.2); BR: (1049.6, 1295.2) |

## Original Event Questions

Distances are to the unchanged provisional human EVENT point, not the text label center.

| Condition | Final output | Geometry | Result |
|---|---|---|---|
| single_event_Z0003_pixels | valid | {"type": "point", "coordinates": [[860, 280]]} | outside-map abstention: False |
| single_event_Z0003_normalized_1000 | error | null | IncompleteThinking |
| single_event_Z0004_pixels | valid | {"type": "point", "coordinates": [[534, 217]]} | 295.2 px |
| single_event_Z0004_normalized_1000 | error | null | IncompleteThinking |

## Completion And Inputs

| Call | Status | Tokens | Image tokens | Time (s) |
|---|---|---:|---:|---:|
| text_Z0003 | valid | 330 | 0 | 26.5 |
| text_Z0004 | valid | 375 | 0 | 28.4 |
| labels_synthetic_pixels_s0 | IncompleteThinking | 4096 | 2695 | 352.4 |
| labels_synthetic_normalized_1000_s0 | IncompleteThinking | 4096 | 2695 | 351.2 |
| single_labels_synthetic_normalized_1000_s0 | IncompleteThinking | 4096 | 2695 | 347.3 |
| single_labels_synthetic_pixels_s0 | valid | 1310 | 2695 | 117.0 |
| single_labels_full_normalized_1000_s0 | valid | 3318 | 2695 | 283.9 |
| single_labels_full_pixels_s0 | valid | 1269 | 2695 | 112.1 |
| single_labels_tile_TL | valid | 365 | 700 | 30.0 |
| single_labels_tile_TR | valid | 1899 | 672 | 147.8 |
| single_labels_tile_BL | valid | 182 | 675 | 16.0 |
| single_labels_tile_BR | valid | 1933 | 648 | 149.4 |
| single_event_Z0003_pixels | valid | 2419 | 2695 | 205.2 |
| single_event_Z0003_normalized_1000 | IncompleteThinking | 4096 | 2695 | 349.1 |
| single_event_Z0004_pixels | valid | 3513 | 2695 | 299.0 |
| single_event_Z0004_normalized_1000 | IncompleteThinking | 4096 | 2695 | 346.2 |
| instruct_labels_synthetic_normalized_1000_s0 | valid | 21 | 2695 | 13.8 |
| instruct_labels_synthetic_pixels_s0 | valid | 21 | 2695 | 12.3 |
| instruct_labels_full_normalized_1000_s0 | valid | 21 | 2695 | 12.3 |
| instruct_labels_full_pixels_s0 | valid | 21 | 2695 | 12.2 |

## Recommended Next Experiment

1. For a new Qwen run, explicitly request 0-1000 coordinates and convert once using the actual supplied image dimensions. Validate bounds and preserve the coordinate mode in every record. Keep previous pixel-output runs unchanged; do not reinterpret old outputs after seeing their errors.
2. Before repeating all event questions, freeze several human-checked label boxes and absent-label controls. Compare both coordinate formats with the same image and inference settings, and use multiple seeds for sampled Thinking. This tests whether the one-label result generalizes.
3. Keep completion rate separate from spatial error. Five Thinking calls exhausted this diagnostic's 4096-token budget, including both normalized event calls. Those two calls cannot establish whether normalization improves event localization. A larger-budget follow-up would test completion, not automatically fix positioning.
4. Require explicit outside-map answers in event evaluation. Regensdorf was correctly extracted from text but was still placed inside this map. Fixed tiling alone is not a solution: the absent BR tile also returned a false location, leaving two candidates.
5. Only after these controls, rerun the ten Zurich events with frozen human-reviewed references. Report answer completion, outside-map detection and event geometry separately. Do not compare this label-center diagnostic directly with historical GPT event-point errors.

No production inference code, human annotation, or old experiment result was changed by this diagnostic.

## Interpretation Boundaries

- Success on text-only questions isolates those particular textual answers, not general historical reasoning ability.
- Synthetic success shows the pipeline/model can use image positions on a simple control. Failure would motivate backend/precision/input checks before blaming historical-map complexity.
- Coordinate effects are assessed within each task; no old pixel output is retrospectively reinterpreted as normalized coordinates.
- Tiling changes search area, context and token count. It does not magnify the source lettering or independently isolate the vision encoder.
- The TR tile also exposes a clipped fragment of the qualified 'unter Altstetten' label. The fixed reference targets the fully visible standalone Altstetten label. This is a tiling ambiguity, not an image-rescaling error; do not silently relabel the reference after seeing predictions.
- One seed, one positive label in the follow-up, and two event questions are insufficient for model rankings or statistical causal claims.
- Official model-card sampling is used, but the 4096-token diagnostic budget is smaller than the model card's recommended 40960 maximum. Incomplete thinking needs a separate completion follow-up, not a claimed location error.

## Model Documentation

- [Qwen3-VL 2D grounding cookbook](https://github.com/QwenLM/Qwen3-VL/blob/main/cookbooks/2d_grounding.ipynb): normalized 0-1000 coordinate examples.
- [Frozen Thinking model card](https://huggingface.co/Qwen/Qwen3-VL-8B-Thinking/blob/92f3c4b4feadd3a016ef468d103bb5f58b2a2c6b/README.md): recommended sampling and generation budget.

## Files

- [Pre-run protocol](../PROTOCOL.md)
- [Structured results and hashes](results.json)
- [Assistant provisional reference boxes](../reference/labels_checked.png)
- [Frozen original input plan](../inputs/plan.json)
- [Declared adaptation](../ADAPTATION.md)
- [Single-target plan](../single/plan.json)
- [Instruct positive-control plan](../instruct_control/plan.json)
- Full final answers and prediction objects are in results.json; raw outputs/token IDs are retained in ../run/attempts.jsonl, ../single/attempts.jsonl and ../instruct_control/attempts.jsonl.
