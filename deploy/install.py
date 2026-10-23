"""First install on the inspected Ubuntu/Caddy host. Run as root with a bundle path."""
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
from datetime import datetime, timezone


def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def main():
    if os.geteuid() != 0:
        raise SystemExit("Run as root")
    bundle = Path(sys.argv[1]).resolve()
    manifest = json.loads((bundle / "manifest.json").read_text())
    for relative, expected in manifest.items():
        path = (bundle / relative).resolve()
        if not path.is_relative_to(bundle) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise SystemExit(f"Bundle integrity failure: {relative}")
    base = Path("/opt/hegrounding")
    data = Path("/var/lib/hegrounding")
    if (base / "current").exists() or data.exists():
        raise SystemExit("Existing deployment: refusing to overwrite server annotations")
    run("apt-get", "update")
    run("apt-get", "install", "-y", "python3-venv", "poppler-utils", env={**os.environ, "DEBIAN_FRONTEND": "noninteractive"})
    if subprocess.run(["id", "hegrounding"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode:
        run("useradd", "--system", "--home-dir", str(data), "--shell", "/usr/sbin/nologin", "hegrounding")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    release = base / "releases" / timestamp
    release.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(bundle / "app", release)
    run("chmod", "-R", "a+rX", str(release))
    run("python3", "-m", "venv", str(base / "venv"))
    run(str(base / "venv/bin/pip"), "install", "-r", str(release / "deploy/requirements-web.txt"))
    with (base / "installed-requirements.txt").open("w") as stream:
        run(str(base / "venv/bin/pip"), "freeze", stdout=stream)
    run(str(base / "venv/bin/python"), "-m", "unittest", "discover", "-s", "benchmark", "-p", "test_public_server.py", cwd=release)
    shutil.copytree(bundle / "data", data)
    run("chown", "-R", "hegrounding:hegrounding", str(data))
    run("chmod", "700", str(data))
    (base / "current").symlink_to(release, target_is_directory=True)
    config = Path("/etc/hegrounding")
    config.mkdir(mode=0o750, exist_ok=True)
    (config / "events.env").write_text('PORT=8877\nURL_PREFIX=""\nWORKSPACE_KIND=main\n')
    (config / "labels.env").write_text('PORT=8879\nURL_PREFIX=/labels\nWORKSPACE_KIND=isolated\n')
    shutil.copy2(release / "deploy/hegrounding@.service", "/etc/systemd/system/hegrounding@.service")
    run("systemctl", "daemon-reload")
    run("systemctl", "enable", "--now", "hegrounding@events", "hegrounding@labels")
    configure_proxy(release)
    print(f"Installed release {timestamp}.")


def configure_proxy(release):
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    password = secrets.token_urlsafe(24)
    hashed = run("caddy", "hash-password", input=password + "\n", text=True, capture_output=True).stdout.strip()
    credentials = Path("/root/hegrounding-access.txt")
    with credentials.open("x") as stream:
        os.chmod(credentials, 0o600)
        stream.write(f"URL: https://experiment.chanlukaka.com\nUsername: eric\nPassword: {password}\n")
    caddyfile = Path("/etc/caddy/Caddyfile")
    original = caddyfile.read_text()
    snippet = Path("/etc/caddy/hegrounding.caddy")
    if "experiment.chanlukaka.com" in original or snippet.exists():
        raise SystemExit("Existing experiment Caddy configuration: inspect before proceeding")
    snippet.write_text((release / "deploy/hegrounding.caddy").read_text().replace("PASSWORD_HASH", hashed))
    snippet.chmod(0o640)
    shutil.chown(snippet, user="root", group="caddy")
    candidate = Path("/etc/caddy/Caddyfile.hegrounding-candidate")
    candidate.write_text(original.rstrip() + "\n\nimport /etc/caddy/hegrounding.caddy\n")
    run("caddy", "validate", "--config", str(candidate), "--adapter", "caddyfile")
    backup = caddyfile.with_name("Caddyfile.before-hegrounding-" + timestamp)
    shutil.copy2(caddyfile, backup)
    shutil.copyfile(candidate, caddyfile)
    try:
        run("systemctl", "reload", "caddy")
    except subprocess.CalledProcessError:
        shutil.copyfile(backup, caddyfile)
        run("systemctl", "reload", "caddy")
        raise
    print(f"Proxy configured. Credentials are in {credentials}; never commit this file.")


if __name__ == "__main__":
    main()
