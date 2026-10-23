"""First review deployment only; preserves portal authentication and existing workspaces."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

ROUND = "assistant_round_20261011"
DATA = Path("/var/lib/hegrounding/reviews") / ROUND
CADDY = Path("/etc/caddy/Caddyfile")
SERVICE = Path("/etc/systemd/system/hegrounding-review.service")


def run(*args):
    subprocess.run(args, check=True)


def install(bundle):
    if DATA.exists() or SERVICE.exists():
        raise SystemExit("Review deployment already exists; refusing to overwrite live reviews")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    release = Path("/opt/hegrounding-review/releases") / stamp
    backup = Path("/var/backups/hegrounding") / f"review-install-{stamp}"
    backup.mkdir(parents=True)
    original = CADDY.read_text()
    marker = "        redir /labels /labels/ 308"
    if original.count(marker) != 1 or "forward_auth 127.0.0.1:3230" not in original or "handle_path /review/*" in original:
        raise SystemExit("Unexpected proxy config; inspect manually before deployment")
    home = Path("/opt/hegrounding/current/benchmark/gui/index.html")
    home_original = home.read_text()
    if '<nav class="home-tools"' not in home_original:
        raise SystemExit("Unexpected homepage layout")
    shutil.copy2(CADDY, backup / "Caddyfile")
    shutil.copy2(home, backup / "index.html")
    with tarfile.open(backup / "initial-review-data.tar.gz", "w:gz") as archive:
        archive.add(bundle / "data", arcname=ROUND)
    shutil.copytree(bundle / "app", release)
    shutil.copytree(bundle / "data", DATA)
    # Only the journal and its directory need writes. Candidate files stay root-owned.
    run("chown", "hegrounding:hegrounding", str(DATA), str(DATA / "human_reviews.jsonl"))
    run("chmod", "750", str(DATA))
    run("chmod", "640", str(DATA / "human_reviews.jsonl"))
    SERVICE.write_text(f"""[Unit]
Description=HE human annotation review
After=network.target

[Service]
User=hegrounding
Group=hegrounding
WorkingDirectory={release}
Environment=PYTHONDONTWRITEBYTECODE=1
Environment=MPLCONFIGDIR=/tmp/hegrounding-review-mpl
ExecStart=/opt/hegrounding/venv/bin/python {release}/benchmark/annotations/{ROUND}/serve_reviews.py --root {DATA} --port 8881 --public-origin https://experiment.chanlukaka.com
Restart=on-failure
RestartSec=3
UMask=0027
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths={DATA}
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
CapabilityBoundingSet=
MemoryMax=512M
TasksMax=48

[Install]
WantedBy=multi-user.target
""")
    route = """        redir /review /review/ 308
        handle_path /review/* {
            reverse_proxy 127.0.0.1:8881 {
                header_up -Authorization
                header_up -Cookie
                header_up -X-Portal-Assertion
            }
        }
"""
    run("systemctl", "daemon-reload")
    try:
        run("systemctl", "enable", "--now", "hegrounding-review")
        run("curl", "--fail", "--silent", "--output", "/dev/null", "-H", "Host: experiment.chanlukaka.com", "http://127.0.0.1:8881/api/reviews", "--retry", "8", "--retry-connrefused", "--retry-delay", "1")
        CADDY.write_text(original.replace(marker, route + marker))
        run("caddy", "validate", "--config", str(CADDY), "--adapter", "caddyfile")
        run("systemctl", "reload", "caddy")
        link = '<a href="/review/" title="Annotation review / 标注审核"><i data-lucide="square-pen"></i>Review / 标注审核</a>'
        start = home_original.index('<nav class="home-tools"')
        position = home_original.index(">", start) + 1
        home.write_text(home_original[:position] + link + home_original[position:])
    except Exception:
        CADDY.write_text(original)
        home.write_text(home_original)
        subprocess.run(["systemctl", "reload", "caddy"])
        subprocess.run(["systemctl", "disable", "--now", "hegrounding-review"])
        raise
    hashes = {name: hashlib.sha256((DATA / name).read_bytes()).hexdigest()
              for name in ["annotations.jsonl", "decisions.json", "human_reviews.jsonl"]}
    print(json.dumps({"release": str(release), "data": str(DATA), "backup": str(backup), "sha256": hashes}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    install(parser.parse_args().bundle.resolve())
