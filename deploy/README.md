# Experiment Website Deployment

Target: `https://experiment.chanlukaka.com`, Ubuntu 24.04 at `66.154.115.22`.
The existing Caddy 2.6 server also hosts other sites. Do not replace its Caddyfile.

## Layout

| URL | Workspace | Loopback backend |
|---|---|---|
| `/`, `/atlas.html` | Historical events and atlas | `127.0.0.1:8877` |
| `/labels/`, `/labels/place-lab.html` | Isolated place-name diagnostics | `127.0.0.1:8879` |

The entire site requires HTTP Basic authentication over HTTPS. This is a private,
single-team annotation deployment, not a multi-user public service with individual roles.
Browsers show a native username/password prompt. The Caddy configuration stores only
a password hash; credentials are generated on the host, not committed to Git.

- Code: `/opt/hegrounding/releases/<timestamp>`, linked by `/opt/hegrounding/current`.
- Python runtime: `/opt/hegrounding/venv`; web-only dependencies, no Torch or model weights.
- Event data: `/var/lib/hegrounding/events`.
- Place-name data: `/var/lib/hegrounding/labels`.
- Services: `hegrounding@events`, `hegrounding@labels`, running as user `hegrounding`.
- Site configuration: `/etc/caddy/hegrounding.caddy`, imported by the existing Caddyfile.
- Access credentials: `/root/hegrounding-access.txt`, mode 0600.

Models cannot be started through the deployed API. Existing predictions remain visible;
new predictions must be generated separately and imported. Neither `.env`, API keys,
model weights, nor the local virtual environment belong in the upload.

## First Install

Create an Alibaba DNS A record: host `experiment`, value `66.154.115.22`.
Leave an AAAA record absent unless the IPv6 address is verified. Caddy obtains and renews
the HTTPS certificate after public DNS points to this server.

From the project root, build a fresh snapshot and upload it into a private staging directory:

```bash
.venv/bin/python deploy/package.py .deploy/bundle-YYYYMMDD
rsync -az -e 'ssh -p 22' .deploy/bundle-YYYYMMDD/ root@66.154.115.22:/root/hegrounding-deploy-YYYYMMDD/
ssh root@66.154.115.22 'python3 /root/hegrounding-deploy-YYYYMMDD/app/deploy/install.py /root/hegrounding-deploy-YYYYMMDD'
```

The installer checks the snapshot manifest, tests public-mode HTTP behavior, installs
two restricted systemd services, validates Caddy before reloading, and preserves the
previous Caddyfile. It refuses to overwrite an existing deployment or annotation directory.
Use a new release for code updates, not this first-install command again.

## Data Ownership And Updates

This deployment creates an independent copy of the local data. There is **no automatic
two-way sync**. Once annotation starts on the website, server data is the authoritative
copy for those edits. Do not run `rsync --delete` from a stale local workspace into
`/var/lib/hegrounding`, and do not overwrite server JSONL files with the deployment snapshot.

For a consistent backup, stop only the two annotation services briefly, archive
`/var/lib/hegrounding`, then start them again. Store a copy off this server. Back up
before updating code or importing batches. The initial deployment does not configure
an automatic off-server backup service.

Update code into a new `/opt/hegrounding/releases/<timestamp>` directory, keep it
root-owned and readable by the service user, switch the `current` symlink, then restart
only the annotation services. Never replace the existing sites' Caddy configuration.

## Verification

- Public requests without credentials return 401; HTTP redirects to HTTPS.
- Both workspace catalogs, map assets and existing predictions load after authentication.
- A valid HTTPS-origin save succeeds on disposable test data; missing or foreign origins,
  stale CSRF tokens, and stale revisions fail.
- The `/labels/` HTML base path, APIs, downloads, images and editor links stay in that workspace.
- Backends listen only on loopback, and inference endpoints are disabled.
- No `.env`, Git directory or arbitrary filesystem paths are served.
- Confirm the other sites still respond after the Caddy reload.

Inspect service state and logs via `systemctl status hegrounding@events hegrounding@labels`
and `journalctl -u hegrounding@events -u hegrounding@labels`. A running backend does not
mean the domain is live: DNS and a publicly trusted certificate must also be verified.

References: [Caddy authentication](https://caddyserver.com/docs/caddyfile/directives/basic_auth),
[subpath proxying](https://caddyserver.com/docs/caddyfile/directives/handle_path).
