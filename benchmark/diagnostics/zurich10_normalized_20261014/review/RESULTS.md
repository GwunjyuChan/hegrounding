# Zurich Ten Events: Normalized Qwen vs GPT-6

Run date: 2026-10-14 (Europe/Zurich).

[Full-resolution interactive comparison](comparison.html) | [Structured diagnostics](diagnostics.json)

## Main Comparison

These are the same ten event questions on ONE map, not ten independent maps. Human references remain provisional.

On the 3 common valid point cases (Z0002, Z0004, Z0006), normalized Qwen mean error is **521.2 px**, versus **28.9 px** for historical GPT-6. Qwen minus GPT-6: **+492.3 px**; Qwen is closer on **0/3** cases.

![Matched point errors](paired_point_errors.png)

Means only cover shared valid point outputs, not all ten questions. Missing, null and non-point outputs are never treated as zero error.

## Coverage And Behavior

| Method | Geometry | Null | Errors | Point n | Point mean px | Point median px | Region hits / scored | Outside-map correct | Seconds |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| Qwen pixel (historical) | 9/10 | 0 | 1 | 5 | 418.9 | 346.1 | 0/2 | False | 501.5 |
| Qwen normalized (new) | 10/10 | 0 | 0 | 5 | 536.7 | 607.6 | 1/2 | False | 154.6 |
| GPT-6 Astra (historical) | 8/10 | 1 | 1 | 3 | 28.9 | 20.9 | 2/2 | True | 108.0 |

The individual-method means above may cover different questions. Use the matched comparisons below for error differences. Region hits mean point-in-polygon, not polygon IoU.

## Interpretation

The strong improvement in the earlier isolated printed-label control does not generalize to this full-passage event run. A coordinate contract can help a model report a location it has identified, but does not itself establish that the model selected the correct event, landmark, river bank or map region.

This run does not isolate which of those reasoning/grounding steps failed. It also does not show that normalization is inherently harmful: the old pixel baseline is historical, prompt dimensions differ, and some cases improve. Keep both results rather than retroactively converting old pixel answers or selecting successful questions.

For the next diagnostic, keep the same map and normalized interface, and compare full-passage event grounding with grounding from a separately extracted location description. Freeze both conditions before inference, preserve spatial qualifiers, and do not provide human coordinates. This would test whether simplifying the textual task helps; it is a proposed follow-up, not a demonstrated fix.

## Matched Subsets

- all_three: n=3; IDs: Z0002, Z0004, Z0006.
- all_three / Qwen pixel (historical): mean 323.1 px, median 342.5 px.
- all_three / Qwen normalized (new): mean 521.2 px, median 607.6 px.
- all_three / GPT-6 Astra (historical): mean 28.9 px, median 20.9 px.
- normalized_vs_gpt6: n=3; IDs: Z0002, Z0004, Z0006.
- normalized_vs_gpt6 / Qwen normalized (new): mean 521.2 px, median 607.6 px.
- normalized_vs_gpt6 / GPT-6 Astra (historical): mean 28.9 px, median 20.9 px.
- normalized_vs_pixel: n=5; IDs: Z0001, Z0002, Z0004, Z0005, Z0006.
- normalized_vs_pixel / Qwen pixel (historical): mean 418.9 px, median 346.1 px.
- normalized_vs_pixel / Qwen normalized (new): mean 536.7 px, median 607.6 px.

## Per Event

| Event | Qwen pixel | Qwen normalized | GPT-6 | Native-pixel detail |
|---|---|---|---|---|
| Z0001 | 383.3 px | 772.0 px | ValueError | [Detail](figures/Z0001.png) |
| Z0002 | 346.1 px | 607.6 px | 18.2 px | [Detail](figures/Z0002.png) |
| Z0003 | wrong in-map location | wrong in-map location | correct outside-map null | [Detail](figures/Z0003.png) |
| Z0004 | 280.6 px | 240.7 px | 20.9 px | [Detail](figures/Z0004.png) |
| Z0005 | 742.1 px | 348.0 px | unscored geometry mismatch | [Detail](figures/Z0005.png) |
| Z0006 | 342.5 px | 715.2 px | 47.5 px | [Detail](figures/Z0006.png) |
| Z0007 | outside region: 419.3 px | inside region | inside region | [Detail](figures/Z0007.png) |
| Z0008 | outside region: 375.9 px | outside region: 515.4 px | inside region | [Detail](figures/Z0008.png) |
| Z0009 | JSONDecodeError | EXCLUDED | EXCLUDED | [Detail](figures/Z0009.png) |
| Z0010 | EXCLUDED | EXCLUDED | EXCLUDED | [Detail](figures/Z0010.png) |

## Controls And Limits

- New inference is Qwen3-VL-8B-Instruct, official nonquantized weights, FP16/MPS, greedy, seed 0, 4096-token cap; not Thinking mode. The same ten passages and questions are retained.
- The model receives an unscaled 1568 x 1760 canvas containing the 1538 x 1754 original, padded only right/bottom. Outputs explicitly use 0-1000 coordinates; conversion uses actual canvas dimensions and rejects positions outside original content.
- No gold, deployment reference, drawn guide, previous model answer or diagnostic crop enters inference. Display crops are produced only after scoring.
- Z0009/Z0010 retain their previous spatial exclusions; Z0003 separately tests outside-map abstention. Existing output errors and geometry mismatches are not repaired. The full ten questions were attempted regardless of scoring exclusions.
- GPT-6 and Qwen pixel are historical results. New Qwen changes both coordinate instruction and declared prompt dimensions (padded rather than original size). Do not interpret it as an isolated fresh coordinate-only ablation or equal-compute model comparison.
- This one-map pilot has provisional references, shared passages and one run per configuration. It cannot establish general model superiority or overall ten-question accuracy. The previous 32 px label-center control is a different task and is not mixed into these event metrics.
- A difference relative to provisional human geometry is not proof of historical correctness. Manual review must remain independent of which model agrees with the current label.

## Audit Files

- [Predeclared protocol](../PROTOCOL.md)
- [Settings and frozen hashes](../manifest.json)
- [Raw responses, prompts, usage and token IDs](../attempts.jsonl)
- [Converted pixel predictions](../predictions.json)
- [Unchanged human snapshot](gold_snapshot.json)
- [Inference runner](../run.py)
