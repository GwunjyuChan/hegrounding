# Zurich Failure Isolation

Declared before inference, 2026-10-13. Exploratory within-model diagnostics, not a new benchmark ranking.

## Questions

1. Does the model extract Regensdorf (Z0003) and Altstetten (Z0004) from the historical text without an image?
2. Can it locate known, clearly printed labels on a simple synthetic image?
3. Does explicit 0-1000 coordinate output help compared with explicit pixel output?
4. Can it locate Altstetten and ZURICH on the historical map, and abstain on absent Regensdorf?
5. Does reducing the search area via fixed tiling help without enlarging or resampling pixels?
6. Do the coordinate effects transfer to the original event questions?

## Matrix: 16 Calls

| Group | Calls | Conditions |
|---|---:|---|
| Text-only | 2 | Original Z0003 and Z0004 passages/questions; no image; answer place name |
| Synthetic control | 2 | Same-sized white canvas with three clear printed names; pixels vs normalized_1000 |
| Historical label centers | 4 | Same three requested labels; full image; pixels vs normalized_1000; seeds 0 and 1 |
| Historical fixed tiles | 4 | All four nonoverlapping tiles, same three label queries; normalized_1000; seed 0 |
| Event localization | 4 | Z0003/Z0004; pixels vs normalized_1000; seed 0 |

Label queries are batched identically across full/tiled/synthetic conditions. Label tasks target printed text centers, not settlement symbols or event locations. Qualified place names such as `unter Altstetten` are not replacements for standalone `Altstetten`.

## Controls

- One checkpoint: Qwen/Qwen3-VL-8B-Thinking revision `92f3c4b4feadd3a016ef468d103bb5f58b2a2c6b`; nonquantized FP16 on MPS.
- Sampling: temperature 1.0, top-p 0.95, top-k 20, repetition penalty 1.0, no presence penalty. These follow the pinned HF model card's VL recommendation.
- Diagnostic output budget: **4096 tokens per call**, not the card's larger maximum. Both prior sampled event answers fit inside this budget. Truncation is reported separately and is not counted as a spatial error. This limits total local inference cost; there is no automatic long-budget retry.
- Reset the predeclared seed before each call. No best-of-N selection or selective retries.
- Same frozen input ZIP as previous Zurich runs. Preserve original 1538 x 1754 pixels; pad to 1568 x 1760. Both coordinate modes use this actual visible padded canvas size in the prompt. This removes canvas-size ambiguity but means the new pixel event arm is not an exact repeat of the older prompt.
- Fixed patch-aligned tiling: TL [0,0,800,896], TR [800,0,1568,896], BL [0,896,800,1760], BR [800,896,1568,1760]. Every tile is tested, not only one chosen around an answer. No scaling, rotation, overlap, extra visual hints or ground-truth-centered crop.
- Normalize relative to the image actually supplied to that call; convert back using that image's width/height, then add the recorded crop origin. Reject invalid/out-of-bound coordinates; never guess a returned coordinate convention.
- Verify actual visual token count, image tensor presence/finite values, processed dimensions, hashes and text-only absence of image tensors. No image or answer is sent to a remote provider.
- Parse only the final answer after `</think>`. No mining draft coordinates, coordinate repairs, forced answer delimiters, or forced early stopping.

## Reference And Analysis

- Synthetic label bounds are exact rendering metadata, saved separately from requests.
- Historical text-label boxes are assistant-drawn provisional references, frozen before these new predictions and explicitly not verified human gold. Prior experiment predictions have already been seen, so this is not a blinded independent human annotation round. These references never enter model requests.
- Z0003 is outside-map; Z0004's old human point remains provisional. Event geometry is never scored against a printed-text box, nor are text-center predictions scored against the old event point.
- Report parsing/completion, target-name correctness, presence/abstention, pixel distance to a reference box, text-center error, and visual overlays separately. Do not merge unlike tasks into one accuracy score.
- Report every tile outcome and false positive, not a gold-selected best tile. A full-map reconstruction is permitted only when exactly one tile returns a non-null point for that name; zero means abstention and multiple means ambiguous, not an oracle choice.
- Compare coordinate modes within each task and both declared seeds where available. A two-seed pilot supports diagnosis, not statistical causal claims.
- Tiling changes visual context and token count as well as search area. Even an improvement does not isolate OCR, attention or visual-encoder internals.
- No edits to production annotations, website data, prior runs, model weights or GPT results.

## Sources

- [Pinned 8B Thinking VL sampling recommendation](https://huggingface.co/Qwen/Qwen3-VL-8B-Thinking/blob/92f3c4b4feadd3a016ef468d103bb5f58b2a2c6b/README.md)
- [Official Qwen3-VL grounding coordinate examples](https://github.com/QwenLM/Qwen3-VL/blob/main/cookbooks/2d_grounding.ipynb)

## Commands

```sh
env MPLCONFIGDIR=/private/tmp/hegrounding-mpl .venv/bin/python benchmark/diagnostics/zurich_failure_isolation_20261013/run.py prepare
env MPLCONFIGDIR=/private/tmp/hegrounding-mpl .venv/bin/python benchmark/diagnostics/zurich_failure_isolation_20261013/run.py run --execute
```
