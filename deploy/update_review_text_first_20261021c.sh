#!/usr/bin/env bash
# 2026-10-21 (batches 1-3): text-first items. Batches 1+2 give 27 map-derived MF items a public-domain source passage
# and add MF0111-MF0137; batch 3 replaces 45 of the 49 remaining AI-paraphrase texts with verbatim public-domain text
# (same IDs, new questions) and adds MF0138-MF0139 (139 events in the round). Run from the repo root on the Mac.
# Replaces update_review_text_first_20261021.sh and ..._20261021b.sh: it works whichever of them was already run. The
# server must be on the 2026-10-20 deploy (state A), batch 1 (state B) or batch 2 (state C), with all four files from
# the same state; otherwise nothing changes.
# serve_reviews.py loads annotations.jsonl and manifest.json at startup, so the service is stopped, the four files are
# swapped, and it is started again. The server files and the review journal are backed up, and the old files are
# restored (with a restart) if any check fails. Map images and serve_reviews.py are unchanged and are not copied.
set -euo pipefail
HOST=root@66.154.115.22
BUNDLE=.deploy/review-update-20261021c
SERVICE=hegrounding-review
FILES="review.html annotations.jsonl manifest.json decisions.json"
A_review_html=bbcf3869f07f3c2176ff62b7dbe4b540f38ff1a077854d8db642ea91ecf90b3c
B_review_html=48f29d4841c175842d247bdd9499ed6ae34bdb1d43c625d20cdd8058e94cc20c
C_review_html=c71f4d9d6fc74034330717faad4ae5a7b543ee394000f749f88e3b9bbf755ecc
NEW_review_html=c6c0f7647c5cc37d75f1f494d5ee05a2a27a55133f7b94cf9f232a872750448f
A_annotations_jsonl=90615cb151abc1046bead8f42dc6520a2c40fdf6fe78985b75c5fd0995315cd5
B_annotations_jsonl=df3cd0fa4731e27548b643d895f9a1d62e9cb463f47ac66396c82370f950cdfb
C_annotations_jsonl=78a58c9ce0b8c94dc760ed72bb33c097d9b99fe6fa490f5c178dd7ba105d14c7
NEW_annotations_jsonl=7c283eb009552afacc16a266921791dd661a80223621786ee34b1057922717c9
A_manifest_json=e31caf0030394db674af28d79d9e7a22fb78a9b332e1a756912c73c9a76c516d
B_manifest_json=d3ff02f010c3c0cff55573f17c0e0e2a35f133c04b0e72c416c3c2095dc77d86
C_manifest_json=c3a1bcc695180cbdc909754fbf85844a98b032d07079b8109fa90d05fd6d77d0
NEW_manifest_json=43a51cd75f3c1e5005620c21aee789f2e3a12c9a96fa03f83af3373c1cb8fcf7
A_decisions_json=7794556a1833a22b35b15d8f25c75f03d5dce7a3c4f0f7cbf637f6a7aa834e98
B_decisions_json=272955870fd265cec6077e19396a8c4d70a08ba989c6673e437442298726a4f0
C_decisions_json=f88c8911120831c7ac516666c605daa59ee8ed88b256bf48a61885c983961c5e
NEW_decisions_json=5842dc5519a3fe0602cc5cb6682d6d664f15c3e478b245554ae8d5ffaf60879e
STAMP=$(date -u +%Y%m%dT%H%M%SZ)

ARGS=()
for f in $FILES; do
  v=${f//./_}; a=A_$v; b=B_$v; c=C_$v; new=NEW_$v
  [ "$(shasum -a 256 "$BUNDLE/$f" | cut -d' ' -f1)" = "${!new}" ] || { echo "Local $BUNDLE/$f changed; stopping."; exit 1; }
  ARGS+=("$f" "${!a}" "${!b}" "${!c}" "${!new}")
done
for f in $FILES; do scp -q "$BUNDLE/$f" "$HOST:/tmp/review-20261021c.$f.new"; done
ssh "$HOST" bash -s -- "$STAMP" "$SERVICE" "${ARGS[@]}" <<'REMOTE'
set -euo pipefail
STAMP=$1 SERVICE=$2; shift 2
DATA=/var/lib/hegrounding/reviews/assistant_round_20261011
BACKUP=/var/backups/hegrounding/review-textfirst-c-$STAMP
sha() { sha256sum "$1" | cut -d' ' -f1; }
NAMES=() AS=() BS=() CS=() NEWS=()
while [ $# -gt 0 ]; do NAMES+=("$1"); AS+=("$2"); BS+=("$3"); CS+=("$4"); NEWS+=("$5"); shift 5; done
STATE=
for i in "${!NAMES[@]}"; do
  f=${NAMES[$i]}
  [ "$(sha "/tmp/review-20261021c.$f.new")" = "${NEWS[$i]}" ] || { echo "Upload of $f corrupted; nothing changed."; exit 1; }
  cur=$(sha "$DATA/$f")
  if [ "$cur" = "${AS[$i]}" ]; then s=A; elif [ "$cur" = "${BS[$i]}" ]; then s=B
  elif [ "$cur" = "${CS[$i]}" ]; then s=C
  elif [ "$cur" = "${NEWS[$i]}" ]; then echo "Server $f is already the new version; nothing changed."; exit 1
  else echo "Server $f is not a known version; nothing changed."; exit 1; fi
  [ -z "$STATE" ] || [ "$STATE" = "$s" ] || { echo "Server files are from different deploys; nothing changed."; exit 1; }
  STATE=$s
done
echo "Server is on state $STATE (A = 2026-10-20 deploy, B = text-first batch 1, C = batch 2)."

systemctl stop "$SERVICE"
JOURNAL=$(sha "$DATA/human_reviews.jsonl")
mkdir -p "$BACKUP"
for f in "${NAMES[@]}"; do cp -p "$DATA/$f" "$BACKUP/$f"; done
cp -p "$DATA/human_reviews.jsonl" "$BACKUP/human_reviews.jsonl"
restore() {
  for f in "${NAMES[@]}"; do cp -p "$BACKUP/$f" "$DATA/$f"; done
  systemctl restart "$SERVICE" || true
  echo "Verification failed; restored the previous files and restarted $SERVICE. Backup: $BACKUP"; exit 1
}
for f in "${NAMES[@]}"; do
  install -o "$(stat -c %u "$DATA/$f")" -g "$(stat -c %g "$DATA/$f")" -m "$(stat -c %a "$DATA/$f")" "/tmp/review-20261021c.$f.new" "$DATA/$f" || restore
done
rm -f /tmp/review-20261021c.*.new
systemctl start "$SERVICE" || restore
get() { curl -fsS --retry 10 --retry-connrefused --retry-delay 1 -H 'Host: experiment.chanlukaka.com' "http://127.0.0.1:8881/$1"; }
for i in "${!NAMES[@]}"; do
  f=${NAMES[$i]}
  [ "$(sha "$DATA/$f")" = "${NEWS[$i]}" ] || restore
  [ "$(get "$f" | sha256sum | cut -d' ' -f1)" = "${NEWS[$i]}" ] || restore
done
CATALOG=$(get api/reviews/export) || restore
case "$CATALOG" in *"\"decisions_sha256\": \"${NEWS[3]}\""*) ;; *) restore ;; esac
[ "$(sha "$DATA/human_reviews.jsonl")" = "$JOURNAL" ] || restore
systemctl is-active --quiet "$SERVICE" || restore
echo "Added the text-first batches 1-3 (139 events). Backup: $BACKUP  Review journal unchanged ($(wc -l < "$DATA/human_reviews.jsonl") lines)."
REMOTE
scp -qr "$HOST:/var/backups/hegrounding/review-textfirst-c-$STAMP" .deploy/
echo "Local copy of the backup: .deploy/review-textfirst-c-$STAMP"
