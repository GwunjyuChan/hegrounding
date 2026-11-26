#!/usr/bin/env bash
# 2026-11-26 (copy of deploy_results_20261125.sh; page now also shows Claude Opus 5.5 and Gemini 4 Neon): static eval results page at https://chenlukaka.com/experiment/results.html (same login as the homepage/review page).
# Adds two files next to the homepage (index.html) in the homepage static folder, which the existing homepage server
# already serves from disk: results.html and results_20261126.json. No service or Caddy change, no restart.
# Map images are NOT uploaded: the page uses the review site's existing assets review/images/<sha256>.<ext>;
# the script checks on the server that every one of them exists before installing.
# Review data (human_reviews.jsonl, difficulty_reviews.jsonl) is never touched; their hashes are checked before/after.
# Anything that would be overwritten is backed up to /var/backups/hegrounding/results-page-<stamp>/.
# Run from the repo root:  bash deploy/deploy_results_20261126.sh            (HEG_HOST=user@host to override the ssh host)
# Needs only the two committed files in benchmark/gui/results_20261126/dist/, python3, ssh/scp and sudo on the server.
# To regenerate dist first (needs the eval package and diagnostics, present on the Mac mini): REBUILD=1 bash deploy/...
set -euo pipefail
HOST=${HEG_HOST:-hegvps}
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
PY=python3; [ -x .venv/bin/python ] && PY=.venv/bin/python
[ "${REBUILD:-0}" = 1 ] && "$PY" benchmark/gui/results_20261126/build_results.py
DIST=benchmark/gui/results_20261126/dist
[ -f "$DIST/results.html" ] && [ -f "$DIST/results_20261126.json" ] || { echo "Missing $DIST/results.html or results_20261126.json"; exit 1; }
HTML_SHA=$(shasum -a 256 "$DIST/results.html" | cut -d' ' -f1)
JSON_SHA=$(shasum -a 256 "$DIST/results_20261126.json" | cut -d' ' -f1)
"$PY" -c "import json,sys;print('\n'.join(sorted({e['image'].split('/')[-1] for e in json.load(open(sys.argv[1]))['events']})))" \
  "$DIST/results_20261126.json" > "${TMPDIR:-/tmp}/results-$STAMP.images"
scp -q "$DIST/results.html" "$HOST:/tmp/results-$STAMP.html"
scp -q "$DIST/results_20261126.json" "$HOST:/tmp/results-$STAMP.json"
scp -q "${TMPDIR:-/tmp}/results-$STAMP.images" "$HOST:/tmp/results-$STAMP.images"; rm -f "${TMPDIR:-/tmp}/results-$STAMP.images"
ssh "$HOST" bash -s -- "$STAMP" "$HTML_SHA" "$JSON_SHA" <<'REMOTE'
set -euo pipefail
STAMP=$1 HTML_SHA=$2 JSON_SHA=$3
SUDO=""; [ "$(id -u)" = 0 ] || SUDO="sudo -n"
GUI=/opt/hegrounding/current/benchmark/gui
DATA=/var/lib/hegrounding/reviews/dataset_v2_20261116
sha() { $SUDO sha256sum "$1" | cut -d' ' -f1; }
cleanup() { rm -f "/tmp/results-$STAMP.html" "/tmp/results-$STAMP.json" "/tmp/results-$STAMP.images"; }
trap cleanup EXIT
[ "$(sha "/tmp/results-$STAMP.html")" = "$HTML_SHA" ] && [ "$(sha "/tmp/results-$STAMP.json")" = "$JSON_SHA" ] || { echo "Upload corrupted; nothing changed."; exit 1; }
$SUDO test -f "$GUI/index.html" || { echo "Homepage folder $GUI not found; nothing changed."; exit 1; }
miss=0; while read -r f; do $SUDO test -f "$DATA/images/$f" || { echo "missing review image: $f"; miss=1; }; done < "/tmp/results-$STAMP.images"
[ $miss = 0 ] || { echo "Some map images are not on the review site; nothing changed."; exit 1; }
journals() { for j in "$DATA/human_reviews.jsonl" "$DATA/difficulty_reviews.jsonl"; do $SUDO test -f "$j" && sha "$j" || echo absent; done; }
BEFORE=$(journals)
BK=/var/backups/hegrounding/results-page-$STAMP; $SUDO mkdir -p "$BK"
for f in results.html results_20261125.json results_20261126.json; do $SUDO test -e "$GUI/$f" && $SUDO cp -p "$GUI/$f" "$BK/$f"; done
OWNER=$($SUDO stat -c %u "$GUI/index.html"); GROUP=$($SUDO stat -c %g "$GUI/index.html")
$SUDO install -o "$OWNER" -g "$GROUP" -m 644 "/tmp/results-$STAMP.html" "$GUI/results.html"
$SUDO install -o "$OWNER" -g "$GROUP" -m 644 "/tmp/results-$STAMP.json" "$GUI/results_20261126.json"
if [ "$(sha "$GUI/results.html")" != "$HTML_SHA" ] || [ "$(sha "$GUI/results_20261126.json")" != "$JSON_SHA" ]; then
  for f in results.html results_20261126.json; do if $SUDO test -e "$BK/$f"; then $SUDO cp -p "$BK/$f" "$GUI/$f"; else $SUDO rm -f "$GUI/$f"; fi; done
  echo "Install check failed; previous state restored."; exit 1
fi
[ "$(journals)" = "$BEFORE" ] || echo "Note: review journals changed during the deploy (normal if someone was reviewing); this script did not write them."
echo "OK: installed $GUI/results.html and $GUI/results_20261126.json. Backup folder: $BK ($($SUDO ls "$BK" | wc -l) previous files)."
echo "Undo: ssh $(hostname) 'sudo rm $GUI/results.html $GUI/results_20261126.json'  (or copy back from $BK)"
REMOTE
echo "Done. Open https://chenlukaka.com/experiment/results.html"
