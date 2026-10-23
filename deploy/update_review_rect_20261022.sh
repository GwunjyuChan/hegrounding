#!/usr/bin/env bash
# 2026-10-22: rectangle tool on the review page (drag out a horizontal box; a button turns the current shape into its
# horizontal box; dragging a box corner keeps it a box). A changed shape now selects 改后接受 by itself.
# Only review.html changes; questions, candidates and the review journal are untouched. Run from the repo root on the
# Mac. The server must be on the page from update_review_i18n_notes_20261021.sh, otherwise nothing changes.
# serve_reviews.py reads review.html on every request, so no restart is needed. The old review.html and the journal
# are backed up, and the old page is restored if any check fails.
set -euo pipefail
HOST=root@66.154.115.22
BUNDLE=.deploy/review-update-20261022a
OLD_review_html=70c0104270483923168f162cf6472bc3efe2bd4eb310655e7655d033c2d4032b
NEW_review_html=456c6ebb543ea066e853a54bc8eb1cd9e2a761a5d5fd10a805c5c06cc138bf3e
annotations_jsonl=7c283eb009552afacc16a266921791dd661a80223621786ee34b1057922717c9
manifest_json=43a51cd75f3c1e5005620c21aee789f2e3a12c9a96fa03f83af3373c1cb8fcf7
decisions_json=5842dc5519a3fe0602cc5cb6682d6d664f15c3e478b245554ae8d5ffaf60879e
STAMP=$(date -u +%Y%m%dT%H%M%SZ)

[ "$(shasum -a 256 "$BUNDLE/review.html" | cut -d' ' -f1)" = "$NEW_review_html" ] || { echo "Local $BUNDLE/review.html changed; stopping."; exit 1; }
scp -q "$BUNDLE/review.html" "$HOST:/tmp/review-rect-20261022.html.new"
ssh "$HOST" bash -s -- "$STAMP" "$OLD_review_html" "$NEW_review_html" "$annotations_jsonl" "$manifest_json" "$decisions_json" <<'REMOTE'
set -euo pipefail
STAMP=$1 OLD=$2 NEW=$3 ANN=$4 MAN=$5 DEC=$6
DATA=/var/lib/hegrounding/reviews/assistant_round_20261011
BACKUP=/var/backups/hegrounding/review-rect-$STAMP
UPLOAD=/tmp/review-rect-20261022.html.new
sha() { sha256sum "$1" | cut -d' ' -f1; }
[ "$(sha "$UPLOAD")" = "$NEW" ] || { echo "Upload corrupted; nothing changed."; exit 1; }
cur=$(sha "$DATA/review.html")
[ "$cur" != "$NEW" ] || { echo "Server review.html already has the rectangle tool; nothing changed."; exit 1; }
[ "$cur" = "$OLD" ] || { echo "Server review.html is not the version from update_review_i18n_notes_20261021.sh; nothing changed."; exit 1; }
[ "$(sha "$DATA/annotations.jsonl")" = "$ANN" ] && [ "$(sha "$DATA/manifest.json")" = "$MAN" ] && [ "$(sha "$DATA/decisions.json")" = "$DEC" ] \
  || { echo "Server data files are not the batch-3 version; nothing changed."; exit 1; }
JOURNAL=$(sha "$DATA/human_reviews.jsonl")
mkdir -p "$BACKUP"
cp -p "$DATA/review.html" "$BACKUP/review.html"
cp -p "$DATA/human_reviews.jsonl" "$BACKUP/human_reviews.jsonl"
restore() {
  cp -p "$BACKUP/review.html" "$DATA/review.html"
  echo "Verification failed; restored the previous review.html. Backup: $BACKUP"; exit 1
}
install -o "$(stat -c %u "$DATA/review.html")" -g "$(stat -c %g "$DATA/review.html")" -m "$(stat -c %a "$DATA/review.html")" "$UPLOAD" "$DATA/review.html" || restore
rm -f "$UPLOAD"
get() { curl -fsS --retry 5 --retry-connrefused --retry-delay 1 -H 'Host: experiment.chanlukaka.com' "http://127.0.0.1:8881/$1"; }
[ "$(sha "$DATA/review.html")" = "$NEW" ] || restore
[ "$(get review.html | sha256sum | cut -d' ' -f1)" = "$NEW" ] || restore
CATALOG=$(get api/reviews/export) || restore
case "$CATALOG" in *"\"decisions_sha256\": \"$DEC\""*) ;; *) restore ;; esac
[ "$(sha "$DATA/human_reviews.jsonl")" = "$JOURNAL" ] || restore
echo "Rectangle tool is live. Backup: $BACKUP  Review journal unchanged ($(wc -l < "$DATA/human_reviews.jsonl") lines)."
REMOTE
scp -qr "$HOST:/var/backups/hegrounding/review-rect-$STAMP" .deploy/
echo "Local copy of the backup: .deploy/review-rect-$STAMP"
