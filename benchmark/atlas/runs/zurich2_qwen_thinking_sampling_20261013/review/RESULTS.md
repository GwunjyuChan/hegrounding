# Recommended Thinking Sampling: Two-Case Pilot

Run date: 2026-10-13. All inference is local. No new GPT API calls were made.

## Main Findings

- Completed thinking blocks: **2/2**; valid final answers (including abstention): **2/2**.
- The previous greedy Thinking runs produced no final answers for these same cases at either 4096 or 8192 tokens.
- New final answers completed within 4096 tokens: **2/2**; within 8192: **2/2**.
- New inference time: **7.0 minutes**; generated tokens: **4800**.
- Z0003: **Placed an outside-map target**. Historical GPT-6 abstained for this outside-map target.
- Z0004: **325.6 px to provisional human label**. Compare Instruct: 280.6 px to provisional human label; GPT-6: 20.9 px to provisional human label.
- Output completion and spatial correctness are separate outcomes. Pixel distances below use unchanged, provisional human labels, not verified ground truth.

## Configuration

[Pinned Qwen3-VL-8B-Thinking model card, VL settings](https://huggingface.co/Qwen/Qwen3-VL-8B-Thinking/blob/92f3c4b4feadd3a016ef468d103bb5f58b2a2c6b/README.md). Sampling enabled; temperature 1.0, top-p 0.95, top-k 20, repetition penalty 1.0, no presence penalty, maximum 40960 generated tokens.

Seed 0 was fixed before inference and reset per request; it is an experimental choice. The official nonquantized checkpoint runs in FP16 on MPS. Source image 1538 x 1754 is padded to 1568 x 1760 without resampling. Model revision, rendered prompts, templates and preprocessing match the earlier greedy Thinking runs.

## Paired Results

| Case | Method | Generated tokens | Time (s) | Result |
|---|---|---:|---:|---|
| Z0003 | Thinking: recommended sampling | 2063 | 181.3 | Placed an outside-map target |
| Z0003 | Thinking: greedy 4096 (previous) | 4096 | 347.6 | IncompleteThinking |
| Z0003 | Thinking: greedy 8192 (previous) | 8192 | 702.7 | IncompleteThinking |
| Z0003 | Instruct: greedy 4096 (previous) | 47 | 15.8 | Placed an outside-map target |
| Z0003 | GPT-6 Astra (historical) | 85 | 7.3 | Outside-map abstention |
| Z0004 | Thinking: recommended sampling | 2737 | 236.1 | 325.6 px to provisional human label |
| Z0004 | Thinking: greedy 4096 (previous) | 4096 | 347.8 | IncompleteThinking |
| Z0004 | Thinking: greedy 8192 (previous) | 8192 | 699.8 | IncompleteThinking |
| Z0004 | Instruct: greedy 4096 (previous) | 47 | 15.3 | 280.6 px to provisional human label |
| Z0004 | GPT-6 Astra (historical) | 53 | 5.4 | 20.9 px to provisional human label |

GPT-6 token accounting and timing come from a historical remote-provider run; they are not directly comparable hardware-throughput measurements.

## New Outputs

### Z0003

Question: After the bridge was laid and the main crossing completed, where was Bontemps's brigade stationed to face Durasof, rather than following Oudinot upstream?

Outcome: **Placed an outside-map target**. Stop reason: `eos`. Thinking tokens: 2015; answer-channel tokens: 48 (including terminating tokens).

Final answer only (unfinished reasoning is not treated as an answer):

```json
{
  "event_id": "Z0003",
  "geometry": {
    "type": "point",
    "coordinates": [
      [420, 580]
    ]
  }
}
```

![Z0003: native-pixel comparison detail](Z0003_detail.png)

[Full-size map comparison](Z0003_full.png)

### Z0004

Question: Where was Klein's division stationed immediately before Massena set it in motion, rather than where Humbert subsequently marched?

Outcome: **325.6 px to provisional human label**. Stop reason: `eos`. Thinking tokens: 2701; answer-channel tokens: 36 (including terminating tokens).

Final answer only (unfinished reasoning is not treated as an answer):

```json
{"event_id": "Z0004", "geometry": {"type": "point", "coordinates": [[500, 350]]}}
```

![Z0004: native-pixel comparison detail](Z0004_detail.png)

[Full-size map comparison](Z0004_full.png)

## Interpretation And Limits

This pilot tests whether the model can finish and emit a usable answer under its recommended sampling configuration. It does not establish a ten-question accuracy improvement or a new model ranking. The cases were preselected for diagnostic value and only one seed was used.

Both sampling and the maximum output budget changed. Finishing before the old budget would rule out the larger cap as necessary for that particular sampled answer, but would not by itself establish reliable improvements across tasks or seeds. A result that requires more than 8192 tokens remains confounded by the larger budget.

Z0003 is an outside-map diagnostic. For Z0004, a smaller distance to the old human point is agreement with a provisional annotation, not independent proof of historical correctness. No labels were overwritten and no draft coordinates were rescued.

Visual inspection of the Z0004 figure: the sampled Thinking point at (500, 350) falls on wooded slopes to the left of Altstetten, near Urdorf. The earlier Instruct point is near Schlieren; the historical GPT-6 point is near the Altstetten settlement label. This map-reading observation supports a remaining visual-localization problem, independently of the exact provisional human pixel. It does not independently verify the historical stationing event.

Do not change model rankings using this pilot. First inspect the final answers and maps; then predeclare a broader recommended-sampling run and review disputed human labels.

## Audit Files

- [Pre-run protocol](../PROTOCOL.md)
- [Machine-readable results and audit hashes](results.json)
- [Actual run manifest](../thinking/manifest.json)
- [Prediction JSON](../thinking/predictions.json)
- Raw outputs, usage and generated token IDs: `../thinking/predictions.attempts.jsonl`.
- The input ZIP and runner snapshot are preserved in `../thinking/`.
