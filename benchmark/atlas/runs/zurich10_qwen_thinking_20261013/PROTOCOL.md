# Zurich 10: Instruct / Thinking / Historical GPT-6 Comparison

Protocol fixed before inference, 2026-10-13 (Europe/Zurich).

- Primary local conditions: official Qwen3-VL-8B-Instruct and Qwen3-VL-8B-Thinking, no 4-bit quantization. Load official BF16 storage weights as float16 on MPS, matching the prior local experiment. This is 16-bit inference, not FP32.
- Pinned revisions: Instruct `0c351dd01ed87e9c1b53cbc748cba10e6187ff3b`; Thinking `92f3c4b4feadd3a016ef468d103bb5f58b2a2c6b`.
- Use the existing frozen `zurich10_20260916_162847/input.zip`, all Z0001-Z0010, identical English text, questions and task instructions.
- Original map: 1538 x 1754; SHA256 `fc5f835f11cd6f7cafefc7183b57d10c0911372149a1c2077f662a6d70570aec`. Pad only right/bottom to 1568 x 1760; explicitly disable resizing and verify RGB hashes and actual image grid. No gold or reference deployment map is sent.
- Greedy decoding, seed 0, 4096 total generated tokens per primary local request, no tools, answer repair, best-of selection or automatic retries. This controlled-budget protocol is not the model authors' recommended maximum-performance sampling configuration.
- Use each checkpoint's official chat template. Thinking's pre-opened reasoning section must close with `</think>` before a final answer can be scored. Never extract draft coordinates from incomplete reasoning. Both final answers use the same strict JSON/geometry validator.
- Any primary request reaching its token limit receives one separate 8192-token supplemental run (same rule for both editions). Keep primary and supplemental results separate; never replace an original failure in primary tables. No further budget increases are planned.
- Load one checkpoint at a time. Runtime excludes model download/load. A one-question memory check is part of the run and is not discarded because of answer quality. Backend failures stop inference and remain in the journal.
- Reuse, do not rerun, GPT-6 Astra results from `zurich10_gpt6_astra_20261007`: identical frozen input and 4096 output-token cap, provider-default reasoning/image processing. No new OpenAI API calls or charges. Internal compute, visual tokens, hardware, run dates and weight precision are not matched across providers.
- Score only after inference in a separate process against the original frozen human snapshot. It is provisional, known to contain mistakes and not independently adjudicated. Do not replace it with model predictions or the unapproved assistant annotation round.
- Retain prior predeclared spatial exclusions Z0009/Z0010. Report Z0003 outside-map abstention separately. Report valid outputs, invalid outputs, abstentions, truncations, same-question point distances and point-in-polygon checks, not a single mixed-geometry accuracy.
- Interpret the comparison as checkpoint performance, not a causal on/off test of reasoning: Instruct and Thinking have different trained weights. Single-map, ten correlated questions cannot establish model-wide superiority.

Sources: [Qwen Thinking model](https://huggingface.co/Qwen/Qwen3-VL-8B-Thinking), [Qwen Instruct model](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct), [Qwen repository](https://github.com/QwenLM/Qwen3-VL).
