#!/usr/bin/env python3
"""Run Claude (Anthropic SDK) or Gemini (google-genai SDK) over tasks.jsonl, same prompts as run_models.py.

Added 2026-11-26 for the closed-model runs on the 260-item set. The request content is built by
run_models.build_messages (the function used for Sol / Qwen / Gemma), then only re-wrapped into each
provider's native message format: system prompt -> system / system_instruction; user turn = image
first, then the identical user_prompt text. Output rows have the same fields as run_models.py
(raw, finish_reason, usage, ...), so convert_predictions.py reads them unchanged.

Only parameters given on the command line are sent; everything else is the provider default.

    python3 code/run_models_native.py --provider anthropic --model claude-opus-5-5 --max-tokens 16000 \
        --ids <...> --out runs/claude-opus-5-5.raw.jsonl
    python3 code/run_models_native.py --provider gemini --model gemini-4-neon --ids <...> \
        --out runs/gemini-4-neon.raw.jsonl

--count-only: count input tokens for every pending task (free endpoints), no generation.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_models import build_messages  # noqa: E402  (same prompt/image construction as the earlier runs)

ANTHROPIC_MAX_IMAGE_BYTES = 5 * 1024 * 1024  # API limit per base64 image (decoded bytes)
ANTHROPIC_MAX_LONG_EDGE = 2576               # model-side resize target for Opus 5.x


def split_messages(msgs):
    """build_messages -> (system text, mime, image bytes, user text); asserts the expected shape."""
    assert msgs[0]["role"] == "system" and msgs[1]["role"] == "user"
    img, txt = msgs[1]["content"]
    assert img["type"] == "image_url" and txt["type"] == "text"
    head, b64 = img["image_url"]["url"].split(",", 1)
    mime = head[len("data:"):-len(";base64")]
    return msgs[0]["content"], mime, base64.b64decode(b64), txt["text"]


def fit_anthropic(mime, data):
    """Images over the 5 MB request limit are resized to the model's own maximum (2576 px long edge,
    what the API would resize to anyway) and sent as PNG. Returns (mime, data, note)."""
    if len(data) <= ANTHROPIC_MAX_IMAGE_BYTES:
        return mime, data, None
    from PIL import Image
    with Image.open(io.BytesIO(data)) as im:
        w, h = im.size
        s = ANTHROPIC_MAX_LONG_EDGE / max(w, h)
        im2 = im.convert("RGB").resize((round(w * s), round(h * s)), Image.LANCZOS)
        buf = io.BytesIO()
        im2.save(buf, "PNG")
        if len(buf.getvalue()) > ANTHROPIC_MAX_IMAGE_BYTES:
            buf = io.BytesIO()
            im2.save(buf, "JPEG", quality=95)
            mime = "image/jpeg"
        else:
            mime = "image/png"
    return mime, buf.getvalue(), f"resized {w}x{h} -> {im2.width}x{im2.height} ({mime}) for 5MB limit"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--provider", choices=["anthropic", "gemini"], required=True)
    ap.add_argument("--package", default=".")
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--api-key-env", default=None)
    ap.add_argument("--max-tokens", type=int, default=None)
    ap.add_argument("--effort", default=None, help="anthropic output_config.effort; omitted unless set")
    ap.add_argument("--thinking-level", default=None, help="gemini thinking_config.thinking_level (e.g. LOW); omitted unless set")
    ap.add_argument("--ids", nargs="*")
    ap.add_argument("--ids-file", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--count-only", action="store_true")
    ap.add_argument("--dump-prompts", default=None, help="write the exact text parts sent, per task, to this JSONL")
    a = ap.parse_args(argv)

    package = Path(a.package)
    tasks = [json.loads(l) for l in (package / "tasks.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    ids = set(a.ids or [])
    if a.ids_file:
        ids |= {l.strip() for l in open(a.ids_file) if l.strip()}
    if ids:
        tasks = [t for t in tasks if t["event_id"] in ids]
    out = Path(a.out)
    done = set()
    if out.exists() and not a.count_only:
        for l in out.read_text(encoding="utf-8").splitlines():
            if l.strip():
                r = json.loads(l)
                if r.get("error") is None:
                    done.add(r["event_id"])
    todo = [t for t in tasks if t["event_id"] not in done][: a.limit]

    if a.provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ[a.api_key_env or "CLAUDE_API_KEY"], max_retries=0)
        base_url = "https://api.anthropic.com/v1/messages"
    else:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=os.environ[a.api_key_env or "GEMINI_API_KEY"])
        base_url = "https://generativelanguage.googleapis.com (google-genai generate_content)"

    dump = open(a.dump_prompts, "w", encoding="utf-8") if a.dump_prompts else None
    total_in = 0
    for i, task in enumerate(todo, 1):
        system, mime, data, user_text = split_messages(build_messages(task, package, ""))
        note = None
        if dump:
            dump.write(json.dumps({"event_id": task["event_id"], "system": system, "user_text": user_text,
                                   "image_mime": mime, "image_bytes_sha256": hashlib.sha256(data).hexdigest()},
                                  ensure_ascii=False) + "\n")
        if a.provider == "anthropic":
            mime, data, note = fit_anthropic(mime, data)
            kwargs = {"model": a.model, "system": system, "messages": [{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": mime,
                                             "data": base64.standard_b64encode(data).decode()}},
                {"type": "text", "text": user_text}]}]}
            params = {"max_tokens": a.max_tokens}
            if a.effort:
                params["output_config"] = {"effort": a.effort}
        else:
            contents = [types.Content(role="user", parts=[types.Part.from_bytes(data=data, mime_type=mime),
                                                          types.Part.from_text(text=user_text)])]
            cfg = {"system_instruction": system}
            if a.max_tokens:
                cfg["max_output_tokens"] = a.max_tokens
            if a.thinking_level:
                cfg["thinking_config"] = types.ThinkingConfig(thinking_level=a.thinking_level)
            params = {k: v for k, v in cfg.items() if k not in ("system_instruction", "thinking_config")}
            if a.thinking_level:
                params["thinking_config"] = {"thinking_level": a.thinking_level}

        if a.count_only:
            if a.provider == "anthropic":
                n = client.messages.count_tokens(**kwargs).input_tokens
            else:
                n = client.models.count_tokens(model=a.model, contents=contents).total_tokens
            total_in += n
            print(f"[{i}/{len(todo)}] {task['event_id']}: input_tokens={n}{' ' + note if note else ''}", flush=True)
            continue

        row = {"event_id": task["event_id"], "model": a.model, "base_url": base_url,
               "prompt_version": task["prompt_version"], "image_sha256": task["image_sha256"],
               "request_params": {k: v for k, v in params.items() if v is not None},
               "image_max_pixels": None, "image_note": note}
        for attempt in range(1, a.retries + 1):
            t0 = time.time()
            try:
                if a.provider == "anthropic":
                    with client.messages.stream(**kwargs, **{k: v for k, v in params.items() if v is not None}) as s:
                        resp = s.get_final_message()
                    text = "".join(b.text for b in resp.content if b.type == "text")
                    row.update(raw=text, finish_reason=resp.stop_reason, response_id=resp.id, served_model=resp.model,
                               usage=resp.usage.model_dump(exclude_none=True),
                               content_types=[b.type for b in resp.content],
                               stop_details=resp.stop_details.model_dump() if getattr(resp, "stop_details", None) else None,
                               error=None)
                else:
                    resp = client.models.generate_content(model=a.model, contents=contents,
                                                          config=types.GenerateContentConfig(**cfg))
                    cand = resp.candidates[0] if resp.candidates else None
                    parts = (cand.content.parts if cand and cand.content and cand.content.parts else [])
                    text = "".join(p.text for p in parts if p.text and not p.thought)
                    row.update(raw=text, finish_reason=str(cand.finish_reason) if cand else None,
                               response_id=resp.response_id, served_model=resp.model_version,
                               usage=resp.usage_metadata.model_dump(exclude_none=True, mode="json") if resp.usage_metadata else None,
                               error=None)
                break
            except Exception as e:  # failed rows are retried on the next run
                row.update(raw=None, error=f"{type(e).__name__}: {e}")
                if attempt < a.retries:
                    time.sleep(2 ** attempt * 2)
        row["latency_s"] = round(time.time() - t0, 2)
        row["time_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with out.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        status = "ERROR " + row["error"][:120] if row["error"] else (row["raw"] or "")[:80].replace("\n", " ")
        print(f"[{i}/{len(todo)}] {task['event_id']}: {status}", flush=True)
    if a.count_only:
        print(f"TOTAL input_tokens={total_in} over {len(todo)} tasks")


if __name__ == "__main__":
    main()
