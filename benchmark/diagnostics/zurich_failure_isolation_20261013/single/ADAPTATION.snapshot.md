# Adaptive Single-Target Follow-Up

Declared after the first four original calls, before any single-target follow-up predictions.

The two text-only calls completed correctly. Both three-target synthetic calibration calls exhausted 4096 tokens without a final answer. Therefore they cannot supply coordinate-error measurements. Continuing the whole multi-target matrix would risk confounding output completion with visual localization.

The original process was interrupted during `labels_full_pixels_s0`. That fifth call has **no scored output**. The first four complete attempts are preserved verbatim in `run/attempts.jsonl`; the remaining original conditions were not completed. This is an adaptive diagnostic, not a completed execution of the original 16-call protocol.

## Follow-Up

- Keep the same images, checkpoint, sampling, 4096-token budget, and seed 0.
- For label tasks, ask only for **Altstetten**. Retain exactly the same JSON schema and label instruction. Only the requested-name list changes from three names to one. The synthetic image still contains all three names.
- Planned calls: synthetic normalized/pixels (2), historical full normalized/pixels (2), all four fixed historical tiles normalized (4), original Z0003/Z0004 event questions in both coordinate modes (4): **12 calls**.
- Safety/interpretability gate: if neither of the two single-target synthetic calls yields a parseable final answer, stop this follow-up before map localization. Do not spend further calls scoring a pipeline without a completed calibration output. Report the remaining tasks as unattempted, not failures.
- No retry/selection among random seeds, no retrospective coordinate reinterpretation, no altered reference boxes, and no reuse of a prediction as gold.
- If calibration completes, continue the entire declared follow-up. The final report includes the original four complete attempts, the cancelled call, all follow-up results, and any unattempted conditions.

This adaptation can show whether target count affects completion in this small setting. It does not isolate all possible schema/prompt/context effects or establish statistical causality. Historical-map references remain provisional and distinct from event annotations.
