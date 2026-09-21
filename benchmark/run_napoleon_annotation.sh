#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PYTHON="${ANNOTATION_PYTHON:-$ROOT/.venv/bin/python}"
if [[ ! -x "$PYTHON" ]]; then
  PYTHON=python3
fi
exec "$PYTHON" benchmark/annotate_geo.py \
  --input benchmark/napoleon_pilot_20.jsonl \
  --output benchmark/napoleon_annotations.jsonl "$@"
