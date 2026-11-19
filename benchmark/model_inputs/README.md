# Model inputs v2 (2026-11-19)

`model_inputs_v2_20261119.jsonl`: one line per item of dataset_v2_20261116 (311 items).

Decision (Lukaka, 2026-11-19 06:11Z): no re-review. The short `event_text` in
`benchmark/annotations/dataset_v2_20261116/annotations.jsonl` stays as the human-review text and all
review verdicts stay valid. The model is given the full verbatim paragraph(s) instead, from this file.

Do NOT add these texts to annotations.jsonl: the review server hashes each whole record
(`candidate_sha256`), so any new field there would mark every review as stale.

Fields
- `model_input_text`: whole paragraph(s) / whole treaty article, verbatim from the source; only obvious
  OCR errors fixed (each fix listed in `notes` and in `.deploy/scan_20261119/full_texts_fixed/fixes_log.json`).
- `model_input_language`: source language. French/German items are given in the original language.
- `origin`: `full_paragraph_checked` (checked or rebuilt against the source / page images in this pass),
  `unchanged` (earlier scan: already whole paragraphs), `PENDING` (needs page scans; currently the old text).
- `file`: the checked text file; `shared_with`: items using the same passage; `rejected_in_review`.

The 12 formerly pending items (MF0101/0103/0104, NC2-SP-013 to 021) were transcribed on 2026-11-19 from page scans downloaded to the Mac mini (benchmark/sources/raw/scans_20261119/ there, with provenance.json).

Rebuild: `python3 build_model_inputs.py` (paths assume the device layout used on 2026-11-19).
