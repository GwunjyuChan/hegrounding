# Deployment Status: 2026-09-29

## Access

- Website: https://experiment.chanlukaka.com/
- Atlas: https://experiment.chanlukaka.com/atlas.html
- Place-name lab: https://experiment.chanlukaka.com/labels/place-lab.html
- Username: `eric`.
- Password: local `.deploy/access.txt` (0600, Git-ignored), also `/root/hegrounding-access.txt` on the server.
- Login page: https://experiment.chanlukaka.com/login.html . Use the same username
  and password. The browser-native Basic Auth prompt was replaced by session login.

## Verified

- Public DNS points to `66.154.115.22`; HTTPS certificate validation succeeds without bypass flags.
- Anonymous requests to pages and APIs in both workspaces return 401.
- Event workspace: 26 map groups, 110 event candidates.
- Independent diagnostic workspace: 8 source samples and 8 saved place-name tasks.
- All 182 migrated data files match the initial snapshot's SHA-256 hashes.
- Preserved append-only history rows: 19 event gold, 42 event predictions,
  16 place gold and 10 place predictions. These are history counts, not unique sample counts.
- Event predictions currently matching active map versions: 0, consistent with the
  copied source data. Older predictions remain stored; they are not automatically
  reprojected onto newer map versions.
- Every reference image, active clean image, workspace page, catalog and place result
  endpoint was checked through authenticated HTTPS. Active images match their saved hashes.
- Public-mode CSRF, origin checks, stale revisions and saves passed on disposable fixtures;
  no test annotation was written into production.
- Inference endpoints are disabled. Backends listen only on `127.0.0.1:8877` and `:8879`.
- Services are enabled at boot, run as `hegrounding`, and are isolated from root and other sites.
- Existing main website returns 200; the jobs site still redirects to its login page.
- Local regression suite: 94 Python tests and 11 JavaScript tests passed.
- Browser preview of the deployed snapshot under `/labels/` rendered the map,
  8 place labels, human points and Qwen overlays correctly.

## Operating Notes

Online annotations are now saved on the server. There is no automatic local/server sync.
Do not overwrite server data with the initial snapshot. See [deployment instructions](README.md).
The initial data snapshot is retained privately at `/root/hegrounding-deploy-20260929/data`;
it is not an ongoing backup of later annotations. Automatic off-server backups are not configured.

The server has about 4 GB RAM and does not host Qwen weights or API credentials.
Run new model evaluations separately and import their outputs.

Initial release: `/opt/hegrounding/releases/20260929T025431Z`.
The Caddy configuration was extended via an import, with the prior configuration backed up.

## Unified Workflow Update

Workflow release: `/opt/hegrounding/releases/20260929T033304Z-workflow`.

- Battle entry now opens the versioned annotation workspace. Unconfigured tasks preview
  the reference map, then require explicit selection of that map or an uploaded alternative.
- Basemap editing is a contextual action within the task, not a peer navigation destination.
- Existing active basemaps and append-only annotation histories are preserved.
- Code-only release update; 183 server data files were hash-checked unchanged while services
  were stopped. No local data snapshot was uploaded over server annotations.
- Pre-update backup: `/root/hegrounding-before-workflow-20260929T033304Z.tar.gz` (0600).
- Local checks: 97 Python tests and 11 JavaScript tests passed. Browser checks on an isolated
  copy covered default preview, confirmation, annotation save, overview progress, re-entry,
  and canceling a crop draft without changing the map or saved annotation.
- Server checks: 24 atlas tests passed before activation; authenticated HTTPS checks for
  both workspaces, all map images, access protection and disabled inference passed afterward.
- Save any current browser draft before refreshing to load the updated interface.

## Login and Independent Place Maps

Installed release: `/opt/hegrounding/releases/20260929T144727Z-login`.

- Site login uses an HTTPS session cookie and `hegrounding-auth` on loopback port 8880.
  HTML requests redirect to `/login.html`; APIs remain protected with JSON 401 responses.
- Login and logout were checked via verified HTTPS. The browser rendered the login page
  when entering the protected place lab. No native authentication dialog is required.
- Place lab HE links to the platform root. `/labels/` opens the place lab directly,
  with an independent map uploader, existing experiments and no European battlefield map.
- Uploaded experiments have their own registry and preserve existing event/label data.
  Model input ZIP export and prediction JSON import support local batch evaluation.
- No Qwen weights or API credentials were added to the public server; inference stays disabled.
- Before switching, 183 data files were hash-checked unchanged. Backup (private root directory):
  `/root/hegrounding-before-login-20260929T144727Z` (research data and prior Caddy snippet).
- Regression checks: 104 local Python tests, 11 JS request tests; 20 targeted tests on the host.
- Post-deploy checks confirmed all reference/active maps and preserved history counts:
  19 event gold, 42 event predictions, 16 place gold and 10 place predictions.
- Session lifecycle, configuration and recovery details: [LOGIN.md](LOGIN.md).

## Bilingual Interface

Installed release: `/opt/hegrounding/releases/20260929T161311Z-i18n`.

- Login, overview, event annotation and place lab have a persistent Chinese/English selector.
- Switching labels does not reload the page or reset drafts, geometry or form values.
  Research passages, questions, custom names, evidence and exported data stay unchanged.
- Local checks: 104 Python tests and 17 JavaScript tests passed. Browser checks covered
  both languages, cross-page preference, draft preservation, desktop and narrow layouts.
- Code-only rollout preserved all 183 server data files by SHA-256 comparison while stopped.
  Backup: `/root/hegrounding-before-i18n-20260929T161311Z`.
- Five auth tests passed on the host. Verified HTTPS checks passed for login/logout,
  public translation assets, both protected workspaces, map images and prediction histories.
- Existing sessions were invalidated by the auth service restart; sign in again if prompted.
- Follow-up: English is now the default for first visits, unknown preferences and unavailable
  browser storage. An explicit saved Chinese preference is still respected. The static script
  was replaced atomically without a service restart; live HTTPS bytes match the local version.
