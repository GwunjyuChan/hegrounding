#!/usr/bin/env python3
"""Minimal VLM evaluation pipeline for place-level map grounding.

The first task to run is place-name grounding:

  python3 benchmark/vlm_eval.py --provider center --task place --limit 20
  python3 benchmark/vlm_eval.py --provider openai --model gpt-4o --task place --sample 20

The same pipeline can also run event-text grounding:

  python3 benchmark/vlm_eval.py --provider openai --model gpt-4o --task event --sample 20

Outputs:
  - per-item JSONL results in benchmark/results/
  - optional gold-vs-prediction visualisations
"""

from __future__ import annotations

import argparse
import base64
import json
import math
import os
import random
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover - checked at runtime for user clarity
    Image = ImageDraw = ImageFont = None

_qwen_cache: dict[str, tuple[Any, Any]] = {}


def _load_qwen(model_id: str) -> tuple[Any, Any]:
    """Lazy-load a Qwen3-VL model and processor, cached for reuse across records."""
    if model_id not in _qwen_cache:
        import torch
        from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

        # Load to CPU first (device_map="mps" deadlocks with transformers sharded loading),
        # then move the whole model to MPS in one shot.
        use_mps = torch.backends.mps.is_available()
        print(f"Loading {model_id} to CPU …", flush=True)
        model = Qwen3VLForConditionalGeneration.from_pretrained(
            model_id, torch_dtype=torch.float32, device_map="cpu"
        )
        if use_mps:
            print("Moving model to MPS …", flush=True)
            model = model.to(torch.device("mps"), dtype=torch.float16)
        processor = AutoProcessor.from_pretrained(model_id)
        print("Model ready.", flush=True)
        _qwen_cache[model_id] = (model, processor)
    return _qwen_cache[model_id]


DEFAULT_BENCHMARK = Path("benchmark/place_benchmark_mixed_200_local.jsonl")
DEFAULT_RESULTS_DIR = Path("benchmark/results")
DEFAULT_VIS_DIR = Path("benchmark/pred_vis")

SYSTEM_PROMPT = (
    "You are evaluating historical Swiss maps. The image is a crop from the "
    "Siegfried map. Coordinates are pixel coordinates with origin at the top-left."
)

PLACE_PROMPT = """\
The image is a {img_w} x {img_h} pixel crop from a historical Swiss Siegfried map.
It covers approximately {crop_km:.0f} km x {crop_km:.0f} km.

Target place name:
{place}

Task:
Find the target place on the map image. Return the location of the place as pixel
coordinates. If the printed label and the settlement centre differ, prefer the
settlement or named-place location rather than a decorative label position.

Return only a JSON object in this exact schema:
{{"x": 123, "y": 456, "confidence": 0.0}}
"""

EVENT_PROMPT = """\
The image is a {img_w} x {img_h} pixel crop from a historical Swiss Siegfried map.
It covers approximately {crop_km:.0f} km x {crop_km:.0f} km.

Historical event description:
{event_text}

Task:
Identify the place associated with this event and locate that place on the map
image. Return the location as pixel coordinates. The target is place-level, not
the exact building, factory, station, road segment, or battlefield point.

Return only a JSON object in this exact schema:
{{"x": 123, "y": 456, "confidence": 0.0}}
"""


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def load_image_b64(path: str | Path) -> str:
    return base64.standard_b64encode(Path(path).read_bytes()).decode("utf-8")


def image_data_url(path: str | Path) -> str:
    return f"data:image/jpeg;base64,{load_image_b64(path)}"


def build_prompt(rec: dict[str, Any], task: str) -> str:
    template = PLACE_PROMPT if task == "place" else EVENT_PROMPT
    return template.format(
        img_w=rec["img_w"],
        img_h=rec["img_h"],
        crop_km=rec["crop_km"],
        place=rec["place"],
        event_text=rec["event_text"],
    )


def parse_prediction(raw: str) -> tuple[int | None, int | None, float | None]:
    text = (raw or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text).strip()

    candidates = [text]
    obj_match = re.search(r"\{.*\}", text, flags=re.S)
    if obj_match:
        candidates.insert(0, obj_match.group(0))

    for candidate in candidates:
        try:
            data = json.loads(candidate)
        except Exception:
            continue
        if isinstance(data, dict) and "x" in data and "y" in data:
            conf = data.get("confidence")
            try:
                conf = float(conf) if conf is not None else None
            except (TypeError, ValueError):
                conf = None
            return int(round(float(data["x"]))), int(round(float(data["y"]))), conf
        if isinstance(data, list) and len(data) >= 2:
            return int(round(float(data[0]))), int(round(float(data[1]))), None

    xy_match = re.search(
        r'"?x"?\s*[:=]\s*(-?\d+(?:\.\d+)?).*?"?y"?\s*[:=]\s*(-?\d+(?:\.\d+)?)',
        text,
        flags=re.S | re.I,
    )
    if xy_match:
        return int(round(float(xy_match.group(1)))), int(round(float(xy_match.group(2)))), None

    pair_match = re.search(r"\[\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\]", text)
    if pair_match:
        return int(round(float(pair_match.group(1)))), int(round(float(pair_match.group(2)))), None

    return None, None, None


def pixel_distance(pred_px: list[int], gold_px: list[int]) -> float:
    return math.hypot(pred_px[0] - gold_px[0], pred_px[1] - gold_px[1])


def select_items(
    records: list[dict[str, Any]],
    ids: list[str],
    limit: int | None,
    sample: int | None,
    seed: int,
) -> list[dict[str, Any]]:
    if ids:
        wanted = set(ids)
        selected = [rec for rec in records if rec["event_id"] in wanted]
        missing = sorted(wanted - {rec["event_id"] for rec in selected})
        if missing:
            raise SystemExit(f"Unknown event ids: {', '.join(missing)}")
        return selected

    if sample:
        rng = random.Random(seed)
        return rng.sample(records, min(sample, len(records)))

    return records[:limit] if limit else records


def call_center(
    rec: dict[str, Any],
    _model: str,
    _task: str,
    _args: argparse.Namespace,
) -> tuple[str, dict[str, Any]]:
    x = int(rec["img_w"] / 2)
    y = int(rec["img_h"] / 2)
    raw = json.dumps({"x": x, "y": y, "confidence": 1.0})
    return raw, {"backend": "center"}


def call_oracle(
    rec: dict[str, Any],
    _model: str,
    _task: str,
    _args: argparse.Namespace,
) -> tuple[str, dict[str, Any]]:
    x, y = rec["gold_px"]
    raw = json.dumps({"x": x, "y": y, "confidence": 1.0})
    return raw, {"backend": "oracle"}


def openai_client(args: argparse.Namespace) -> Any:
    from openai import OpenAI

    api_key = os.environ.get(args.api_key_env)
    if args.base_url and not api_key:
        api_key = "EMPTY"
    kwargs: dict[str, Any] = {"api_key": api_key} if api_key else {}
    if args.base_url:
        kwargs["base_url"] = args.base_url
    return OpenAI(**kwargs)


def call_openai(
    rec: dict[str, Any],
    model: str,
    task: str,
    args: argparse.Namespace,
) -> tuple[str, dict[str, Any]]:
    client = openai_client(args)
    prompt = build_prompt(rec, task)
    request: dict[str, Any] = {
        "model": model,
        "input": [
            {
                "role": "system",
                "content": [{"type": "input_text", "text": SYSTEM_PROMPT}],
            },
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": image_data_url(rec["image"])},
                ],
            },
        ],
        "max_output_tokens": args.max_output_tokens,
    }
    if args.reasoning_effort and (model.startswith("gpt-5") or model.startswith("o")):
        request["reasoning"] = {"effort": args.reasoning_effort}

    response = client.responses.create(**request)
    raw = getattr(response, "output_text", "") or str(response)
    usage = getattr(response, "usage", None)
    return raw.strip(), {"backend": "openai", "usage": usage.model_dump() if usage else None}


def call_openai_chat(
    rec: dict[str, Any],
    model: str,
    task: str,
    args: argparse.Namespace,
) -> tuple[str, dict[str, Any]]:
    """Use OpenAI Chat Completions format.

    This is useful both for OpenAI models and for local/open-source servers that
    expose an OpenAI-compatible `/v1/chat/completions` endpoint.
    """

    client = openai_client(args)
    prompt = build_prompt(rec, task)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_data_url(rec["image"])}},
                ],
            },
        ],
        max_tokens=120,
    )
    raw = response.choices[0].message.content or ""
    usage = getattr(response, "usage", None)
    return raw.strip(), {"backend": "openai-chat", "usage": usage.model_dump() if usage else None}


def call_anthropic(
    rec: dict[str, Any],
    model: str,
    task: str,
    _args: argparse.Namespace,
) -> tuple[str, dict[str, Any]]:
    import anthropic

    client = anthropic.Anthropic()
    prompt = build_prompt(rec, task)
    message = client.messages.create(
        model=model,
        max_tokens=120,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": load_image_b64(rec["image"]),
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    )
    raw = "".join(block.text for block in message.content if getattr(block, "type", "") == "text")
    usage = getattr(message, "usage", None)
    return raw.strip(), {"backend": "anthropic", "usage": usage.model_dump() if usage else None}


def call_qwen(
    rec: dict[str, Any],
    model: str,
    task: str,
    args: argparse.Namespace,
) -> tuple[str, dict[str, Any]]:
    """Local Qwen3-VL inference via HuggingFace transformers (MPS on Apple Silicon)."""
    import torch
    from qwen_vl_utils import process_vision_info

    vlm_model, processor = _load_qwen(model)
    prompt = build_prompt(rec, task)
    image_path = f"file://{Path(rec['image']).resolve()}"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image_path},
                {"type": "text", "text": prompt},
            ],
        },
    ]
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    )
    device = next(vlm_model.parameters()).device
    inputs = inputs.to(device)

    with torch.no_grad():
        out_ids = vlm_model.generate(
            **inputs,
            max_new_tokens=args.max_output_tokens or 120,
            do_sample=False,
        )

    generated = out_ids[0][inputs["input_ids"].shape[1]:]
    raw = processor.decode(generated, skip_special_tokens=True)
    return raw.strip(), {"backend": "qwen-transformers", "model": model}


CALLERS = {
    "center": call_center,
    "oracle": call_oracle,
    "openai": call_openai,
    "openai-chat": call_openai_chat,
    "anthropic": call_anthropic,
    "qwen": call_qwen,
}


def make_result(
    rec: dict[str, Any],
    raw: str,
    meta: dict[str, Any],
    args: argparse.Namespace,
    error: str | None = None,
) -> dict[str, Any]:
    x, y, confidence = parse_prediction(raw) if error is None else (None, None, None)
    pred_px = [x, y] if x is not None and y is not None else None
    dist_px = dist_m = None
    hit = False

    if pred_px is not None:
        dist_px = pixel_distance(pred_px, rec["gold_px"])
        dist_m = dist_px * rec["m_per_px"]
        hit = dist_m <= args.tolerance_m

    hit_250m = dist_m <= 250 if dist_m is not None else False
    hit_500m = dist_m <= 500 if dist_m is not None else False
    hit_1000m = dist_m <= 1000 if dist_m is not None else False

    return {
        "event_id": rec["event_id"],
        "task": args.task,
        "provider": args.provider,
        "model": args.model,
        "place": rec["place"],
        "event_type": rec.get("event_type", ""),
        "time": rec.get("time", ""),
        "image": rec["image"],
        "gold_px": rec["gold_px"],
        "pred_px": pred_px,
        "dist_px": round(dist_px, 2) if dist_px is not None else None,
        "dist_m": round(dist_m, 2) if dist_m is not None else None,
        "hit": hit,
        "hit_250m": hit_250m,
        "hit_500m": hit_500m,
        "hit_1000m": hit_1000m,
        "tolerance_m": args.tolerance_m,
        "m_per_px": rec["m_per_px"],
        "confidence": confidence,
        "raw": raw,
        "error": error,
        "meta": meta,
    }


def summarise(results: list[dict[str, Any]], tolerance_m: float) -> str:
    valid = [r for r in results if r.get("dist_m") is not None]
    if not valid:
        return "No valid predictions."

    distances = sorted(float(r["dist_m"]) for r in valid)
    n = len(valid)
    mean = sum(distances) / n
    median = distances[n // 2]
    hits = sum(1 for r in valid if r.get("hit"))
    parse_failures = sum(1 for r in results if r.get("pred_px") is None and not r.get("error"))
    api_errors = sum(1 for r in results if r.get("error"))

    hits_250 = sum(1 for r in valid if r.get("hit_250m"))
    hits_500 = sum(1 for r in valid if r.get("hit_500m"))
    hits_1000 = sum(1 for r in valid if r.get("hit_1000m"))
    beyond_1000 = n - hits_1000

    lines = [
        f"valid={n}/{len(results)}",
        f"hit@250m={hits_250 / n:.1%}",
        f"hit@500m={hits_500 / n:.1%}",
        f"hit@1000m={hits_1000 / n:.1%}",
        f"beyond_1000m={beyond_1000 / n:.1%}",
        f"median={median:.1f}m",
        f"mean={mean:.1f}m",
        f"parse_failures={parse_failures}",
        f"errors={api_errors}",
    ]
    if tolerance_m not in (500, 1000):
        lines.insert(4, f"hit@{tolerance_m:.0f}m={hits / n:.1%}")

    by_type: dict[str, list[float]] = defaultdict(list)
    for result in valid:
        by_type[result.get("event_type", "")].append(float(result["dist_m"]))
    for event_type, vals in sorted(by_type.items()):
        vals = sorted(vals)
        type_hits = sum(v <= tolerance_m for v in vals)
        lines.append(
            f"{event_type}: n={len(vals)}, hit={type_hits / len(vals):.1%}, "
            f"median={vals[len(vals)//2]:.1f}m"
        )

    return " | ".join(lines)


def load_font(size: int) -> Any:
    if ImageFont is None:
        return None
    for name in [
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]:
        if Path(name).exists():
            try:
                return ImageFont.truetype(name, size)
            except Exception:
                pass
    return ImageFont.load_default()


def draw_crosshair(draw: Any, xy: list[int], color: tuple[int, int, int], radius: int = 17) -> None:
    x, y = xy
    draw.ellipse([x - radius, y - radius, x + radius, y + radius], outline=(255, 255, 255), width=5)
    draw.line([x - radius - 12, y, x + radius + 12, y], fill=(255, 255, 255), width=5)
    draw.line([x, y - radius - 12, x, y + radius + 12], fill=(255, 255, 255), width=5)
    draw.ellipse([x - radius, y - radius, x + radius, y + radius], outline=color, width=3)
    draw.line([x - radius - 12, y, x + radius + 12, y], fill=color, width=3)
    draw.line([x, y - radius - 12, x, y + radius + 12], fill=color, width=3)
    draw.ellipse([x - 4, y - 4, x + 4, y + 4], fill=color)


def visualise_prediction(result: dict[str, Any], vis_dir: Path) -> Path | None:
    if Image is None or ImageDraw is None:
        return None
    image_path = Path(result["image"])
    if not image_path.exists():
        return None

    vis_dir.mkdir(parents=True, exist_ok=True)
    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    m_per_px = result.get("m_per_px") or result.get("crop_km", 6) * 1000 / result.get("img_w", 1024)
    r250 = max(3, int(250 / m_per_px))
    r500 = max(4, int(500 / m_per_px))
    r1000 = max(8, int(1000 / m_per_px))
    gx, gy = result["gold_px"]
    draw.ellipse([gx - r1000, gy - r1000, gx + r1000, gy + r1000], outline=(255, 165, 0), width=2)
    draw.ellipse([gx - r500, gy - r500, gx + r500, gy + r500], outline=(220, 30, 30), width=2)
    draw.ellipse([gx - r250, gy - r250, gx + r250, gy + r250], outline=(180, 0, 220), width=2)
    draw.ellipse([gx - 4, gy - 4, gx + 4, gy + 4], fill=(220, 30, 30))
    if result.get("pred_px") is not None:
        draw_crosshair(draw, result["pred_px"], (30, 100, 230), radius=13)
        draw.line(result["gold_px"] + result["pred_px"], fill=(40, 40, 40), width=2)

    bar_h = 88
    out = Image.new("RGB", (img.width, img.height + bar_h), (30, 30, 30))
    out.paste(img, (0, 0))
    draw = ImageDraw.Draw(out)
    font_lg = load_font(15)
    font_sm = load_font(12)

    pred = result.get("pred_px")
    dist = result.get("dist_m")
    status = "HIT" if result.get("hit") else "MISS"
    line1 = f"{result['event_id']} | {result['place']} | {result.get('event_type', '')} | {status}"
    line2 = f"gold(red)={result['gold_px']} pred(blue)={pred} dist={dist}m"
    line3 = f"task={result['task']} provider={result['provider']} model={result['model']}"
    draw.text((10, img.height + 6), line1, fill=(255, 225, 90), font=font_lg)
    draw.text((10, img.height + 32), line2, fill=(220, 220, 220), font=font_sm)
    draw.text((10, img.height + 58), line3, fill=(170, 170, 170), font=font_sm)

    out_path = vis_dir / f"{result['event_id']}.jpg"
    out.save(out_path, quality=92)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--run-name", default=None)
    parser.add_argument("--provider", choices=sorted(CALLERS), default="center")
    parser.add_argument("--model", default="gpt-4o")
    parser.add_argument(
        "--base-url",
        default=None,
        help="Optional OpenAI-compatible base URL, e.g. http://localhost:8000/v1",
    )
    parser.add_argument(
        "--api-key-env",
        default="OPENAI_API_KEY",
        help="Environment variable containing the API key. Local servers may use a dummy key.",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path(".env"),
        help="Optional .env file loaded before API clients are created.",
    )
    parser.add_argument("--task", choices=["place", "event"], default="place")
    parser.add_argument("--ids", nargs="*", default=[])
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--sample", type=int, default=None)
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--sleep", type=float, default=0.2)
    parser.add_argument("--tolerance-m", type=float, default=500.0)
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        default=1000,
        help="Responses API output token budget. Includes reasoning tokens for reasoning models.",
    )
    parser.add_argument(
        "--reasoning-effort",
        default="minimal",
        help="Reasoning effort for gpt-5/o-series models. Use empty string to omit.",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--vis-dir", type=Path, default=DEFAULT_VIS_DIR)
    parser.add_argument("--no-vis", action="store_true")
    args = parser.parse_args()
    load_env_file(args.env_file)

    records = select_items(load_jsonl(args.benchmark), args.ids, args.limit, args.sample, args.seed)
    run_name = args.run_name or f"{args.task}_{args.provider}_{args.model.replace('/', '-')}"
    out_path = args.results_dir / f"{run_name}.jsonl"
    vis_dir = args.vis_dir / run_name

    if args.dry_run:
        for rec in records[: min(3, len(records))]:
            print(f"\n--- {rec['event_id']} {rec['place']} ---")
            print(build_prompt(rec, args.task))
        print(f"\nDry run only. Selected {len(records)} records.")
        return

    args.results_dir.mkdir(parents=True, exist_ok=True)
    if out_path.exists() and args.no_resume:
        out_path.unlink()

    done: set[str] = set()
    if out_path.exists() and not args.no_resume:
        for line in out_path.open(encoding="utf-8"):
            if line.strip():
                done.add(json.loads(line)["event_id"])
        if done:
            print(f"Resuming {out_path}: {len(done)} already done")

    caller = CALLERS[args.provider]
    new_results: list[dict[str, Any]] = []
    with out_path.open("a", encoding="utf-8") as fh:
        for rec in records:
            if rec["event_id"] in done:
                continue

            try:
                raw, meta = caller(rec, args.model, args.task, args)
                result = make_result(rec, raw, meta, args)
            except Exception as exc:
                result = make_result(rec, "", {}, args, error=str(exc))

            if not args.no_vis:
                vis_path = visualise_prediction(result, vis_dir)
                if vis_path is not None:
                    result["prediction_image"] = str(vis_path)

            fh.write(json.dumps(result, ensure_ascii=False) + "\n")
            fh.flush()
            new_results.append(result)

            dist = result.get("dist_m")
            if result.get("error"):
                print(f"ERR  {rec['event_id']} {rec['place']}: {result['error']}")
            elif dist is None:
                print(f"PARSE {rec['event_id']} {rec['place']}: {result['raw'][:80]!r}")
            else:
                mark = "HIT " if result["hit"] else "MISS"
                print(f"{mark} {rec['event_id']} {rec['place'][:32]:32s} pred={result['pred_px']} dist={dist:.1f}m")

            time.sleep(args.sleep)

    all_results = []
    if out_path.exists():
        all_results = [json.loads(line) for line in out_path.open(encoding="utf-8") if line.strip()]
    print(f"\nResults: {out_path}")
    if not args.no_vis:
        print(f"Prediction visualisations: {vis_dir}")
    print("New run:", summarise(new_results, args.tolerance_m))
    print("All in file:", summarise(all_results, args.tolerance_m))
    print("Event types:", dict(Counter(r.get("event_type", "") for r in all_results)))


if __name__ == "__main__":
    main()
