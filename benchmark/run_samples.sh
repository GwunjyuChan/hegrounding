#!/usr/bin/env bash
set -euo pipefail

BENCHMARK="benchmark/place_benchmark_mixed_200_clean_v3.jsonl"
PROVIDER="openai"
MODEL="gpt-4o"
TASK="place"
SAMPLE="20"
SEED="42"
SLEEP="0.2"
NO_RESUME=""

usage() {
  cat <<'EOF'
Usage:
  bash benchmark/run_samples.sh [options]

Examples:
  bash benchmark/run_samples.sh
  bash benchmark/run_samples.sh --sample 5
  bash benchmark/run_samples.sh --sample 20 --task event
  bash benchmark/run_samples.sh --sample 50 --model gpt-4o
  bash benchmark/run_samples.sh --all --task place

Options:
  --benchmark PATH      Benchmark JSONL path.
  --provider NAME       center | oracle | openai | openai-chat | anthropic.
  --model NAME          Model name.
  --task NAME           place | event.
  --sample N            Random sample size.
  --seed N              Random seed.
  --sleep SECONDS       Sleep between API calls.
  --all                 Run all benchmark items instead of a sample.
  --no-resume           Start a fresh result file.
  -h, --help            Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --benchmark)
      BENCHMARK="$2"
      shift 2
      ;;
    --provider)
      PROVIDER="$2"
      shift 2
      ;;
    --model)
      MODEL="$2"
      shift 2
      ;;
    --task)
      TASK="$2"
      shift 2
      ;;
    --sample)
      SAMPLE="$2"
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
    --all)
      SAMPLE=""
      shift
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

if [[ ! -f "$BENCHMARK" ]]; then
  echo "Benchmark not found: $BENCHMARK" >&2
  exit 1
fi

if [[ -n "$SAMPLE" ]]; then
  RUN_MODEL="${MODEL//\//-}"
  RUN_NAME="${PROVIDER}_${RUN_MODEL}_${TASK}_${SAMPLE}_clean_v3_seed${SEED}"
  SAMPLE_ARGS=(--sample "$SAMPLE" --seed "$SEED")
else
  RUN_MODEL="${MODEL//\//-}"
  RUN_NAME="${PROVIDER}_${RUN_MODEL}_${TASK}_all_clean_v3"
  SAMPLE_ARGS=()
fi

echo "Benchmark: $BENCHMARK"
echo "Provider:  $PROVIDER"
echo "Model:     $MODEL"
echo "Task:      $TASK"
echo "Run name:  $RUN_NAME"

python3 benchmark/vlm_eval.py \
  --provider "$PROVIDER" \
  --model "$MODEL" \
  --task "$TASK" \
  --benchmark "$BENCHMARK" \
  "${SAMPLE_ARGS[@]}" \
  --sleep "$SLEEP" \
  --run-name "$RUN_NAME" \
  $NO_RESUME
