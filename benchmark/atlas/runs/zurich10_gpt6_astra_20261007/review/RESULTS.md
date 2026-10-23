# Zurich Ten Questions: GPT-6 Astra Comparison

**[高清交互对比：逐题、同步缩放、原像素导出](comparison.html)**

**[中文详细报告：附图、逐题误差与模型能力分析](../../../../../ZURICH_MODEL_COMPARISON_REPORT_2026-10-08.md)**

Completed (local time): 2026-10-08T00:00:21.180762+02:00. Run started 2026-10-07.

## Controls

Same frozen ten passages/questions, prompt, original 1538x1754 PNG and 4096-token output limit as GPT-5. No gold or deployment map was sent. No tools, coordinate repair, retries or answer selection.
GPT-6 API uses provider-default image detail/reasoning, as did GPT-5. Original PNG bytes are sent unchanged; server-side image processing is not verified. Native Qwen uses a padded 1568x1760 canvas with no resampling. This is not an identical vision-token or reasoning-compute budget comparison.
Z0009 (road question vs point gold) and Z0010 (city question vs retreat-line gold) are predeclared exclusions. Z0003 is outside the frozen map and tests abstention. Human labels remain provisional.

## Summary

| Model | Valid geometry | Abstained | Errors | Valid point n | Mean px | Median px | Point in polygon | Seconds |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| qwen_native | 9/10 | 0 | 1 | 5 | 418.9 | 346.1 | 0/2 | 501.5 |
| gpt5 | 9/10 | 0 | 1 | 4 | 534.7 | 515.6 | 0/2 | 461.8 |
| gpt6_astra | 8/10 | 1 | 1 | 3 | 28.9 | 20.9 | 2/2 | 108.0 |

Valid geometry is not accuracy. Means above may use different successful subsets; use paired comparisons below.

## Paired Point Comparisons

- GPT-6 Astra vs qwen_native: n=3, IDs: Z0002, Z0004, Z0006.
  Mean error: 323.1 -> 28.9 px; reduction 91.1%. Improved 3, worsened 0.
- GPT-6 Astra vs gpt5: n=2, IDs: Z0004, Z0006.
  Mean error: 484.4 -> 34.2 px; reduction 92.9%. Improved 2, worsened 0.

## Per Question

| Event | Qwen native | GPT-5 | GPT-6 Astra | Image |
|---|---|---|---|---|
| Z0001 | 距人工点 383.3 px | 距人工点 924.9 px | ValueError | [Z0001](Z0001_comparison.png) |
| Z0002 | 距人工点 346.1 px | JSONDecodeError | 距人工点 18.2 px | [Z0002](Z0002_comparison.png) |
| Z0003 | 图外仍定位 | 图外仍定位 | 图外拒答 | [Z0003](Z0003_comparison.png) |
| Z0004 | 距人工点 280.6 px | 距人工点 182.5 px | 距人工点 20.9 px | [Z0004](Z0004_comparison.png) |
| Z0005 | 距人工点 742.1 px | 距人工点 244.9 px | 几何不同/无可用真值，未评分 | [Z0005](Z0005_comparison.png) |
| Z0006 | 距人工点 342.5 px | 距人工点 786.3 px | 距人工点 47.5 px | [Z0006](Z0006_comparison.png) |
| Z0007 | 区域外 419.3 px | 区域外 85.5 px | 区域内 0.0 px | [Z0007](Z0007_comparison.png) |
| Z0008 | 区域外 375.9 px | 区域外 103.9 px | 区域内 0.0 px | [Z0008](Z0008_comparison.png) |
| Z0009 | JSONDecodeError | 已运行，不评分 | 已运行，不评分 | [Z0009](Z0009_comparison.png) |
| Z0010 | 已运行，不评分 | 已运行，不评分 | 已运行，不评分 | [Z0010](Z0010_comparison.png) |

## Limits and Audit

GPT-6 Astra returned medium reasoning effort in all ten response metadata records. All API responses completed; Z0001 failed local geometry validation because it returned coordinates [311,100] instead of [[311,100]]. It was not repaired or retried. Z0005 returned a polygon against point gold and is therefore not included in point-distance means. Missing/truncated reasoning text is not treated as an answer.
Single map and one run per model, provisional gold, historical baselines, and provider-default inference settings do not establish general model superiority. Paired success-only error omits failures; always read coverage and error counts together. The API token budget includes reasoning, and truncated responses are retained as failures.
No current website layers or human annotations were changed. These results belong only to the frozen map version.

| Model | Input tokens | Output tokens | Total tokens |
|---|---:|---:|---:|
| qwen_native | 31381 | 4519 | 35900 |
| gpt5 | 10583 | 27696 | 38279 |
| gpt6_astra | 36633 | 2286 | 38919 |

- [Predictions](../predictions.json)
- [Raw responses and usage](../predictions.attempts.jsonl)
- [Run settings](../manifest.json)
- [Structured diagnostics](diagnostics.json)
- [All comparison images](all_comparisons.png)

Model API documentation: https://developers.openai.com/api/docs/models/gpt-6-astra
