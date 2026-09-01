#!/usr/bin/env bash
set -euo pipefail

TAG="clean_v3"
SEED="42"
SLEEP="0.2"
IMG_SIZE="1024"
CROP_KM="6.0"
MAX_OFFSET_FRAC="0.30"

REBUILD_EVENTS_V3="0"
SKIP_GEOCODE="0"
SKIP_FETCH_CROPS="0"
SKIP_ASSEMBLE="0"
SKIP_REVIEW="0"
SKIP_QUALITY="0"
SKIP_VIS="0"

EVAL_MODE="none"
EVAL_SAMPLE=""
EVAL_TASK="place"
EVAL_PROVIDER="openai"
EVAL_MODEL="gpt-4o"
EVAL_SLEEP="0.2"
TOLERANCE_M="500"
NO_RESUME=""

EVENTS=""
GEOCODES=""
GOLD=""
CROPS_DIR=""
BENCHMARK=""
REVIEW_CSV=""
ANNOTATED_REVIEW_CSV=""
QUALITY_CSV=""
VIS_DIR=""

usage() {
  cat <<'EOF'
Usage:
  bash benchmark/run_full_pipeline.sh [options]

Default pipeline:
  1. geocode events
  2. fetch missing Siegfried map crops
  3. assemble benchmark JSONL
  4. create review CSV
  5. run automatic crop-quality check
  6. create gold-marker visualisations
  7. create annotated review CSV

By default, VLM evaluation is not run. Enable it with --eval-sample N or --eval-all.

Examples:
  bash benchmark/run_full_pipeline.sh
  bash benchmark/run_full_pipeline.sh --skip-fetch-crops
  bash benchmark/run_full_pipeline.sh --eval-sample 20
  bash benchmark/run_full_pipeline.sh --eval-all --eval-task place --eval-model gpt-4o
  bash benchmark/run_full_pipeline.sh --rebuild-events-v3

Options:
  --tag NAME              Dataset tag. Default: clean_v3.
  --seed N                Seed for crop offsets and eval sampling. Default: 42.
  --sleep SECONDS         Sleep between map WMS requests. Default: 0.2.
  --img-size N            Map crop image size in pixels. Default: 1024.
  --crop-km N             Map crop width/height in km. Default: 6.0.
  --max-offset-frac N     Random crop offset fraction. Default: 0.30.

  --events PATH           Override events JSONL path.
  --geocodes PATH         Override geocodes JSONL path.
  --gold PATH             Override gold JSONL path.
  --crops-dir PATH        Override crop image directory.
  --benchmark PATH        Override benchmark JSONL path.
  --review-csv PATH       Override review CSV path.
  --quality-csv PATH      Override crop-quality CSV path.
  --vis-dir PATH          Override gold-marker visualisation directory.

  --rebuild-events-v3     Rebuild the current clean_v3 event list from clean_v2
                          plus archived candidate pools and manual rejects.
  --skip-geocode          Skip geocoding.
  --skip-fetch-crops      Skip map crop fetching.
  --skip-assemble         Skip benchmark assembly.
  --skip-review           Skip review CSV and annotated review CSV.
  --skip-quality          Skip automatic crop-quality check.
  --skip-vis              Skip gold-marker visualisations.

  --eval-sample N         Run VLM eval on N random items.
  --eval-all              Run VLM eval on all benchmark items.
  --eval-task NAME        place | event. Default: place.
  --eval-provider NAME    openai | openai-chat | anthropic | center | oracle.
  --eval-model NAME       Model name. Default: gpt-4o.
  --eval-sleep SECONDS    Sleep between VLM calls. Default: 0.2.
  --tolerance-m N         HIT threshold in metres. Default: 500.
  --no-resume             Pass --no-resume to VLM eval.
  -h, --help              Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tag)
      TAG="$2"
      shift 2
      ;;
    --seed)
      SEED="$2"
      shift 2
      ;;
    --sleep)
      SLEEP="$2"
      shift 2
      ;;
    --img-size)
      IMG_SIZE="$2"
      shift 2
      ;;
    --crop-km)
      CROP_KM="$2"
      shift 2
      ;;
    --max-offset-frac)
      MAX_OFFSET_FRAC="$2"
      shift 2
      ;;
    --events)
      EVENTS="$2"
      shift 2
      ;;
    --geocodes)
      GEOCODES="$2"
      shift 2
      ;;
    --gold)
      GOLD="$2"
      shift 2
      ;;
    --crops-dir)
      CROPS_DIR="$2"
      shift 2
      ;;
    --benchmark)
      BENCHMARK="$2"
      shift 2
      ;;
    --review-csv)
      REVIEW_CSV="$2"
      shift 2
      ;;
    --quality-csv)
      QUALITY_CSV="$2"
      shift 2
      ;;
    --vis-dir)
      VIS_DIR="$2"
      shift 2
      ;;
    --rebuild-events-v3)
      REBUILD_EVENTS_V3="1"
      shift
      ;;
    --skip-geocode)
      SKIP_GEOCODE="1"
      shift
      ;;
    --skip-fetch-crops)
      SKIP_FETCH_CROPS="1"
      shift
      ;;
    --skip-assemble)
      SKIP_ASSEMBLE="1"
      shift
      ;;
    --skip-review)
      SKIP_REVIEW="1"
      shift
      ;;
    --skip-quality)
      SKIP_QUALITY="1"
      shift
      ;;
    --skip-vis)
      SKIP_VIS="1"
      shift
      ;;
    --eval-sample)
      EVAL_MODE="sample"
      EVAL_SAMPLE="$2"
      shift 2
      ;;
    --eval-all)
      EVAL_MODE="all"
      shift
      ;;
    --eval-task)
      EVAL_TASK="$2"
      shift 2
      ;;
    --eval-provider)
      EVAL_PROVIDER="$2"
      shift 2
      ;;
    --eval-model)
      EVAL_MODEL="$2"
      shift 2
      ;;
    --eval-sleep)
      EVAL_SLEEP="$2"
      shift 2
      ;;
    --tolerance-m)
      TOLERANCE_M="$2"
      shift 2
      ;;
    --no-resume)
      NO_RESUME="--no-resume"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$EVENTS" ]]; then
  EVENTS="extraction/place_events_mixed_200_${TAG}.jsonl"
fi
if [[ -z "$GEOCODES" ]]; then
  GEOCODES="maps/place_geocodes_mixed_200_${TAG}.jsonl"
fi
if [[ -z "$GOLD" ]]; then
  GOLD="maps/place_gold_coords_mixed_200_${TAG}.jsonl"
fi
if [[ -z "$CROPS_DIR" ]]; then
  CROPS_DIR="maps/place_crops_mixed_200_${TAG}"
fi
if [[ -z "$BENCHMARK" ]]; then
  BENCHMARK="benchmark/place_benchmark_mixed_200_${TAG}.jsonl"
fi
if [[ -z "$REVIEW_CSV" ]]; then
  REVIEW_CSV="benchmark/place_review_mixed_200_${TAG}.csv"
fi
if [[ -z "$QUALITY_CSV" ]]; then
  QUALITY_CSV="benchmark/crop_quality_mixed_200_${TAG}.csv"
fi
if [[ -z "$VIS_DIR" ]]; then
  VIS_DIR="benchmark/place_vis_mixed_200_${TAG}_all"
fi
ANNOTATED_REVIEW_CSV="${REVIEW_CSV%.csv}_annotated.csv"

echo "Tag:       $TAG"
echo "Events:    $EVENTS"
echo "Geocodes:  $GEOCODES"
echo "Gold:      $GOLD"
echo "Crops:     $CROPS_DIR"
echo "Benchmark: $BENCHMARK"
echo "Review:    $REVIEW_CSV"
echo "Quality:   $QUALITY_CSV"
echo "Vis:       $VIS_DIR"

if [[ "$REBUILD_EVENTS_V3" == "1" ]]; then
  if [[ "$TAG" != "clean_v3" ]]; then
    echo "--rebuild-events-v3 is tied to tag clean_v3; current tag is $TAG" >&2
    exit 2
  fi

  echo
  echo "[1/8] Rebuilding clean_v3 events"
  python3 benchmark/refill_benchmark_events.py \
    --base-events extraction/place_events_mixed_200_clean_v2.jsonl \
    --quality-csv benchmark/crop_quality_mixed_200_clean_v2.csv \
    --reject-ids M0016 M0040 M0041 \
    --reject-places Varese Bodensee "Lindau D" Stockach Livigno "Berner Oberland" \
    --prefer-source-event-ids L0110 L0116 L0118 \
    --candidate-events \
      archive/benchmark_data_2026-08-05_pre_clean_v2/extraction/place_events_war_candidates_local.jsonl \
      archive/benchmark_data_2026-08-05_pre_clean_v2/extraction/place_events_transport_local.jsonl \
      archive/benchmark_data_2026-08-05_pre_clean_v2/extraction/place_events_industrial_local.jsonl \
    --output "$EVENTS" \
    --reject-output benchmark/rejected_events_clean_v3.csv
else
  echo
  echo "[1/8] Using existing events"
fi

if [[ ! -f "$EVENTS" ]]; then
  echo "Events file not found: $EVENTS" >&2
  exit 1
fi

if [[ "$SKIP_GEOCODE" == "0" ]]; then
  echo
  echo "[2/8] Geocoding places"
  python3 maps/geocode_places.py \
    --events "$EVENTS" \
    --output "$GEOCODES" \
    --sleep "$SLEEP"
else
  echo
  echo "[2/8] Skipping geocoding"
fi

if [[ "$SKIP_FETCH_CROPS" == "0" ]]; then
  echo
  echo "[3/8] Fetching missing Siegfried crops"
  python3 maps/fetch_siegfried_crops.py \
    --events "$EVENTS" \
    --geocodes "$GEOCODES" \
    --crops-dir "$CROPS_DIR" \
    --gold "$GOLD" \
    --img-size "$IMG_SIZE" \
    --crop-km "$CROP_KM" \
    --max-offset-frac "$MAX_OFFSET_FRAC" \
    --seed "$SEED" \
    --sleep "$SLEEP"
else
  echo
  echo "[3/8] Skipping crop fetching"
fi

if [[ "$SKIP_ASSEMBLE" == "0" ]]; then
  echo
  echo "[4/8] Assembling benchmark"
  python3 benchmark/assemble_place_benchmark.py \
    --events "$EVENTS" \
    --geocodes "$GEOCODES" \
    --gold "$GOLD" \
    --output "$BENCHMARK"
else
  echo
  echo "[4/8] Skipping benchmark assembly"
fi

if [[ "$SKIP_REVIEW" == "0" ]]; then
  echo
  echo "[5/8] Creating review CSV"
  python3 benchmark/make_place_review_csv.py \
    --events "$EVENTS" \
    --geocodes "$GEOCODES" \
    --gold "$GOLD" \
    --output "$REVIEW_CSV"
else
  echo
  echo "[5/8] Skipping review CSV"
fi

if [[ "$SKIP_QUALITY" == "0" ]]; then
  echo
  echo "[6/8] Checking crop quality"
  python3 benchmark/check_crop_quality.py \
    --benchmark "$BENCHMARK" \
    --output "$QUALITY_CSV"
else
  echo
  echo "[6/8] Skipping crop-quality check"
fi

if [[ "$SKIP_VIS" == "0" ]]; then
  echo
  echo "[7/8] Creating gold-marker visualisations"
  python3 benchmark/visualise.py \
    --all \
    --benchmark "$BENCHMARK" \
    --vis-dir "$VIS_DIR"
else
  echo
  echo "[7/8] Skipping visualisations"
fi

if [[ "$SKIP_REVIEW" == "0" && "$SKIP_VIS" == "0" ]]; then
  echo
  echo "[8/8] Creating annotated review CSV"
  python3 - "$REVIEW_CSV" "$ANNOTATED_REVIEW_CSV" "$VIS_DIR" <<'PY'
import csv
import sys
from pathlib import Path

review_csv = Path(sys.argv[1])
annotated_csv = Path(sys.argv[2])
vis_dir = Path(sys.argv[3])

with review_csv.open(encoding="utf-8-sig", newline="") as fh:
    rows = list(csv.DictReader(fh))

if rows:
    fieldnames = list(rows[0].keys())
    if "annotated_image" not in fieldnames:
        insert_at = fieldnames.index("image") + 1 if "image" in fieldnames else len(fieldnames)
        fieldnames.insert(insert_at, "annotated_image")
    for row in rows:
        row["annotated_image"] = str(vis_dir / f"{row['event_id']}.jpg")
else:
    fieldnames = []

annotated_csv.parent.mkdir(parents=True, exist_ok=True)
with annotated_csv.open("w", encoding="utf-8-sig", newline="") as fh:
    writer = csv.DictWriter(fh, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {len(rows)} annotated review rows -> {annotated_csv}")
PY
else
  echo
  echo "[8/8] Skipping annotated review CSV"
fi

echo
echo "[check] Validating outputs"
python3 - "$BENCHMARK" "$QUALITY_CSV" "$VIS_DIR" "$ANNOTATED_REVIEW_CSV" <<'PY'
import csv
import json
import sys
from collections import Counter
from pathlib import Path

benchmark = Path(sys.argv[1])
quality_csv = Path(sys.argv[2])
vis_dir = Path(sys.argv[3])
annotated_csv = Path(sys.argv[4])

rows = []
if benchmark.exists():
    with benchmark.open(encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]

print("benchmark_rows:", len(rows))
print("event_type:", dict(Counter(row.get("event_type", "") for row in rows)))
print("missing_images:", sum(1 for row in rows if not Path(row.get("image", "")).exists()))
print("vis_count:", len(list(vis_dir.glob("*.jpg"))) if vis_dir.exists() else 0)
print("annotated_review_exists:", annotated_csv.exists())

if quality_csv.exists():
    with quality_csv.open(encoding="utf-8-sig", newline="") as fh:
        quality = list(csv.DictReader(fh))
    print("crop_quality:", dict(Counter(row.get("crop_status", "") for row in quality)))
    print("non_ok:", [(row.get("event_id"), row.get("place"), row.get("crop_status")) for row in quality if row.get("crop_status") != "ok"])
else:
    print("crop_quality: missing")
PY

if [[ "$EVAL_MODE" != "none" ]]; then
  echo
  echo "[eval] Running VLM eval"
  if [[ "$EVAL_MODE" == "sample" ]]; then
    RUN_NAME="${EVAL_PROVIDER}_${EVAL_TASK}_${EVAL_SAMPLE}_${TAG}_seed${SEED}_tol${TOLERANCE_M}"
    EVAL_SELECT_ARGS=(--sample "$EVAL_SAMPLE" --seed "$SEED")
  else
    RUN_NAME="${EVAL_PROVIDER}_${EVAL_TASK}_all_${TAG}_tol${TOLERANCE_M}"
    EVAL_SELECT_ARGS=()
  fi

  python3 benchmark/vlm_eval.py \
    --provider "$EVAL_PROVIDER" \
    --model "$EVAL_MODEL" \
    --task "$EVAL_TASK" \
    --benchmark "$BENCHMARK" \
    "${EVAL_SELECT_ARGS[@]}" \
    --sleep "$EVAL_SLEEP" \
    --tolerance-m "$TOLERANCE_M" \
    --run-name "$RUN_NAME" \
    $NO_RESUME
else
  echo
  echo "[eval] Skipped. Use --eval-sample N or --eval-all to run VLM evaluation."
fi
