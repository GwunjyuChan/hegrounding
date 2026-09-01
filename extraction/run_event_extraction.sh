#!/usr/bin/env bash
set -euo pipefail

TAG="extracted"
INPUT="hls-data-v2.json"
SEED="42"
WAR_TARGET="100"
TRANSPORT_TARGET="50"
INDUSTRIAL_TARGET="50"
QUIET="--quiet"

usage() {
  cat <<'EOF'
Usage:
  bash extraction/run_event_extraction.sh [options]

Extract a 200-item mixed place-event set from the local HLS dump:
  - 100 war/conflict events
  - 50 transport events
  - 50 industrial events

The default output is:
  extraction/place_events_mixed_200_extracted.jsonl

Examples:
  bash extraction/run_event_extraction.sh
  bash extraction/run_event_extraction.sh --tag trial1
  bash extraction/run_event_extraction.sh --tag clean_v4 --seed 7

Options:
  --tag NAME              Output tag. Default: extracted.
  --input PATH            HLS dump JSON path. Default: hls-data-v2.json.
  --seed N                Random seed. Default: 42.
  --war-target N          Number of war/conflict events. Default: 100.
  --transport-target N    Number of transport events. Default: 50.
  --industrial-target N   Number of industrial events. Default: 50.
  --verbose               Show extraction details.
  -h, --help              Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tag)
      TAG="$2"
      shift 2
      ;;
    --input)
      INPUT="$2"
      shift 2
      ;;
    --seed)
      SEED="$2"
      shift 2
      ;;
    --war-target)
      WAR_TARGET="$2"
      shift 2
      ;;
    --transport-target)
      TRANSPORT_TARGET="$2"
      shift 2
      ;;
    --industrial-target)
      INDUSTRIAL_TARGET="$2"
      shift 2
      ;;
    --verbose)
      QUIET=""
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

if [[ ! -f "$INPUT" ]]; then
  echo "HLS dump not found: $INPUT" >&2
  exit 1
fi

WAR_OUT="extraction/place_events_war_${TAG}.jsonl"
TRANSPORT_OUT="extraction/place_events_transport_${TAG}.jsonl"
INDUSTRIAL_OUT="extraction/place_events_industrial_${TAG}.jsonl"
MIXED_OUT="extraction/place_events_mixed_200_${TAG}.jsonl"

echo "Input:      $INPUT"
echo "Tag:        $TAG"
echo "Seed:       $SEED"
echo "War:        $WAR_OUT ($WAR_TARGET)"
echo "Transport:  $TRANSPORT_OUT ($TRANSPORT_TARGET)"
echo "Industrial: $INDUSTRIAL_OUT ($INDUSTRIAL_TARGET)"
echo "Mixed:      $MIXED_OUT"

python3 extraction/extract_place_events_from_hls_dump.py \
  --input "$INPUT" \
  --profile war \
  --target "$WAR_TARGET" \
  --seed "$SEED" \
  --output "$WAR_OUT" \
  $QUIET

python3 extraction/extract_place_events_from_hls_dump.py \
  --input "$INPUT" \
  --profile transport \
  --target "$TRANSPORT_TARGET" \
  --seed "$SEED" \
  --output "$TRANSPORT_OUT" \
  $QUIET

python3 extraction/extract_place_events_from_hls_dump.py \
  --input "$INPUT" \
  --profile industrial \
  --target "$INDUSTRIAL_TARGET" \
  --seed "$SEED" \
  --output "$INDUSTRIAL_OUT" \
  $QUIET

python3 extraction/combine_place_event_sets.py \
  --inputs "$WAR_OUT" "$TRANSPORT_OUT" "$INDUSTRIAL_OUT" \
  --output "$MIXED_OUT"

echo
echo "Next step:"
echo "  bash benchmark/run_full_pipeline.sh --tag $TAG"
