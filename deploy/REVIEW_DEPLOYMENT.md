# Online Annotation Review

Deployed 2026-10-17. This is the current editable AI-candidate review workspace, separate from atlas gold and model runs.

## Entry And Data

- URL: <https://experiment.chanlukaka.com/review/>
- Resume event: <https://experiment.chanlukaka.com/review/review.html#MF0017>
- Website homepage now includes `Review / 标注审核`.
- Authentication uses the existing portal at `chanlukaka.com`, via Caddy's existing `forward_auth` on port 3230. No credentials or portal permissions were changed. Older deployment documents describing Basic auth or the old 8880 session gateway do not describe the current live authentication.
- Snapshot: 110 candidates on 26 annotation maps; 63 events have saved review records. Latest decisions at migration: 45 accepted, 1 modified accepted, 10 rejected, 1 needs changes, 1 needs evidence, 5 pending.
- Original candidate geometry and local reviews were not changed. Acceptance still does not automatically promote a record to benchmark gold.

**Use the online URL on both computer and phone from now on.** Server reviews are authoritative for subsequent online edits. The old `http://127.0.0.1:8771/` is an independent local copy; there is no two-way synchronization. Do not copy stale local JSONL over server data.

The editor supports point/line/polygon drawing, vertex edits, undo/redo, reference-map viewing, acceptance/rejection and notes. Saving appends a revision; stale revisions are rejected. Unsaved drafts belong only to that browser tab, not to other devices. Save before switching devices, and reload reviews on a previously opened device before editing the same event.

## Runtime

| Item | Location |
| --- | --- |
| Service | `hegrounding-review.service` |
| Listener | `127.0.0.1:8881`, not a public port |
| Code | `/opt/hegrounding-review/releases/20261017T203545Z` |
| Data | `/var/lib/hegrounding/reviews/assistant_round_20261011` |
| Append-only journal | `human_reviews.jsonl` under the data directory |
| Proxy configuration | `/etc/caddy/Caddyfile`, `/review/*` after the existing auth gate |
| Pre-install backup | `/var/backups/hegrounding/review-install-20261017T203545Z` |

The deployment has separate code and data directories. Existing event and place-name workspaces remain unchanged, except for a homepage navigation link. Caddy configuration and the prior homepage were backed up before editing. The installer refuses to overwrite an existing review deployment.

The online HTML is about 876 KB instead of the offline viewer's 23 MB. Original map bytes are served on demand from content-addressed `images/` assets; dimensions and coordinate systems are unchanged. The offline viewer still embeds images for standalone use.

## Verification

- 50 Python tests passed, including public HTTPS origin, CSRF, geometry validation, stale revisions and asset allowlisting.
- Desktop/mobile browser tests use disposable journals, never production reviews.
- Both offline-asset and online-asset packages passed the browser suite. The online package was additionally tested under a disposable `/review/` reverse proxy, including edit/save/reload, images and conflict handling.
- Caddy configuration validated and reloaded; review, event and label services are active.
- Unauthenticated public page and API requests return 303 to the existing login flow. Backend health returns 200; listener remains loopback-only.
- Original candidate and decision hashes match local files. Initial journal SHA-256: `dcf3d943dfd4cd0c973a621ea8483addc072acbf75be5e35e6ea40cf6fb39611`.
- Authenticated live-browser verification completed after explicit permission to access the portal and the user signing in. The homepage review link opens `/review/`; MF0017's map, saved acceptance, reviewer and notes controls load, and vertex editing is enabled. At a 390 x 844 viewport the page has no horizontal overflow and the map loads at its native 1302 x 1302 pixels. The viewport was reset afterward. No production review was edited or saved during verification; persistence testing remains confined to disposable test journals.
- The review progress counter shows 58/110 non-pending decisions at verification. The migrated 63 saved event records include five pending records. Homepage atlas progress is a separate workflow and is not the AI-candidate review counter.

## Backups And Updates

The initial migration snapshot is backed up on the server and downloaded to local `.deploy/review-initial-backup-20261017.tar.gz`. No recurring backup job or automatic synchronization was configured by this deployment.

Before later updates, briefly stop only `hegrounding-review`, archive its data directory, and restart it. Keep a copy off-server. Preserve review logs and original candidate versions when deploying code updates. Do not rerun the first-install script against existing data.

Authenticated read-only export: <https://experiment.chanlukaka.com/review/api/reviews/export>. This exports latest review state, not the full append-only history; use a filesystem backup to retain every revision.

Build a new first-install bundle locally with `deploy/package_reviews.py <new-output-directory>`. It includes only required code, candidate data, map images and a locked snapshot of the review journal, not `.env`, API keys, model weights or unrelated project files.
