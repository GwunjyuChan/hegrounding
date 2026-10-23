"""Shared helpers for text-first items (2026-10-21): verbatim passages cut from archive.org OCR by anchors.

A passage runs from the line holding `start` to the line holding `end` (both inclusive, matched after
whitespace collapsing). Lines matching any `drop` regex (running heads, page numbers, footnotes) are removed,
end-of-line hyphens are joined, whitespace collapsed, then only the listed OCR fixes are applied, each recorded.
Nothing is retyped by hand. Geometry is an assistant draft for human review.
"""
import hashlib, json, pathlib, re, sys

RAW = "benchmark/sources/raw/"

def _norm(s):
    return re.sub(r"\s+", " ", s).strip()

def build_passage(path, start, end, drop=(), fixes=()):
    lines = pathlib.Path(path).read_text(errors="replace").split("\n")
    norm = [_norm(l) for l in lines]
    try:
        a = next(i for i, l in enumerate(norm) if start in l)
        b = next(i for i in range(a, len(norm)) if end in norm[i])
    except StopIteration:
        sys.exit(f"{path}: anchors not found: {start!r} .. {end!r}")
    kept, dropped = [], []
    for i in range(a, b + 1):
        if any(re.search(p, norm[i]) for p in drop):
            dropped.append(i + 1)
        else:
            kept.append(lines[i])
    text = "\n".join(kept)
    text = re.sub(r"-\s*\n\s*", "", text)
    text = _norm(text)
    text = text[text.index(start):]
    text = text[:text.index(end) + len(end)]
    applied = []
    for old, new in fixes:
        if old in text:
            text = text.replace(old, new); applied.append(f"{old.strip()} -> {new.strip()}")
    return text, dict(first_line=a + 1, last_line=b + 1, dropped_lines=dropped, ocr_corrections=applied)

def sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()

def make_records(spec):
    """spec: dict(battle_id, image, img_w, img_h, map_url, map_provenance, sources={key: dict(file, archive_id,
    citation, source_kind)}, passages={key: dict(source, start, end, pages, drop, fixes)}, items=[...])"""
    img_sha = sha256(spec["image"])
    built = {}
    for k, p in spec["passages"].items():
        src = spec["sources"][p["source"]]
        built[k] = build_passage(src["file"], p["start"], p["end"], p.get("drop", ()), p.get("fixes", ()))
    out = []
    for it in spec["items"]:
        p = spec["passages"][it["passage"]]
        src = spec["sources"][p["source"]]
        text, info = built[it["passage"]]
        model_text = p.get("translation", text)
        if it["text_evidence"] not in model_text:
            sys.exit(f"{it['event_id']}: text_evidence not in model input text")
        if it.get("source_evidence") and it["source_evidence"] not in text:
            sys.exit(f"{it['event_id']}: source_evidence not in original passage")
        out.append({
            "event_id": it["event_id"], "replaces": it.get("replaces"), "battle_id": spec["battle_id"],
            "image": spec["image"], "img_w": spec["img_w"], "img_h": spec["img_h"], "map_asset_sha256": img_sha,
            "map_url": spec["map_url"], "map_provenance": spec["map_provenance"],
            "event_text": model_text, "source_text": text,
            "text_kind": "assistant_translation_of_verbatim_source_paragraph" if "translation" in p else "verbatim_source_passage",
            "input_language": "en", "source_language": p.get("lang", "en"), "source_kind": src["source_kind"],
            "source_citation": f"{src['citation']}, {p['pages']}",
            "article_url": f"https://archive.org/details/{src['archive_id']}",
            "source_rights": "public_domain", "source_rights_basis": src["rights_basis"],
            "source_archive_id": src["archive_id"], "source_raw_file": src["file"],
            "source_raw_sha256": sha256(src["file"]),
            "source_raw_lines": f"{info['first_line']}-{info['last_line']}",
            "source_raw_dropped_lines": info["dropped_lines"], "ocr_corrections": info["ocr_corrections"],
            "time": it["time"], "target_question": it["question"], "question_zh": it["question_zh"],
            "answer_zh": it["answer_zh"], "text_evidence": it["text_evidence"], "map_evidence": it["map_evidence"],
            "draft_geometry": it["geometry"], "geometry_source": it.get("geometry_source", "assistant_draft"),
            "confidence_draft": it["confidence_draft"], "spatial_tags": [it["tag"]],
            "status": it.get("status", "pending"), "curation_status": "draft_needs_human_review",
            "created": spec["created"],
        })
        if "translation" in p:
            out[-1].update(translation_by="Claude", translation_review="pending",
                           source_evidence=it.get("source_evidence"))
    return out, built

def write(spec, path):
    out, built = make_records(spec)
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(path, len(out))
    for k, (t, info) in built.items():
        print(f"\n== {k} ({len(t.split())} words) lines {info['first_line']}-{info['last_line']} "
              f"dropped={info['dropped_lines']} fixes={info['ocr_corrections']}\n{t}")

def map_record(image):
    """Map metadata (size, URL, provenance) as already recorded for the MF candidates."""
    for l in open("benchmark/map_first_candidates.jsonl"):
        r = json.loads(l)
        if r["image"] == image:
            return r
    sys.exit(f"no map record for {image}")

SIBORNE_V1 = dict(
    file=RAW + "siborne1844_v1_india.history.resource.40765_djvu.txt", archive_id="india.history.resource.40765",
    citation="William Siborne, History of the War in France and Belgium, in 1815, 1st ed., vol. I "
             "(London: T. & W. Boone, 1844)",
    source_kind="secondary_history (author surveyed the field and corresponded with surviving officers)",
    rights_basis="published 1844; author d. 1849")
SIBORNE_DROP = [r"^\d{1,5}$", r"^June\.?$", r"^1\dth of$", r"^of$", r"^\*$", r"^HISTORY OF THE WAR IN$",
                r"^FRANCE AND BELGIUM IN 1[8S][1I]5\.?$", r"^\|$"]
