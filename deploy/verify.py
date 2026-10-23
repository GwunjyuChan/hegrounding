"""Read-only production checks. Run on the host; credentials never leave stdin."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

DOMAIN = "experiment.chanlukaka.com"
ORIGIN = "https://" + DOMAIN
SESSION = None


def request(path, authenticated=True, method="GET", headers=(), body=None, response_headers=False):
    config = ""
    if authenticated:
        assert SESSION, 'Login required before authenticated verification'
        config += 'header = ' + json.dumps('Cookie: ' + SESSION) + '\n'
    if body is not None:
        config += 'data = ' + json.dumps(json.dumps(body)) + '\n'
        config += 'header = "Content-Type: application/json"\n'
    args = ["curl", "--silent", "--show-error", "--noproxy", "*", "--include", "--max-time", "30", "--resolve",
            f"{DOMAIN}:443:127.0.0.1", "--config", "-", "--request", method,
            "--write-out", "\n%{http_code}", ORIGIN + path]
    for header in headers:
        args.extend(["--header", header])
    if method == "POST" and body is None:
        args.extend(["--data", "{}"])
    result = subprocess.run(args, input=config.encode(), capture_output=True, check=True)
    raw, status = result.stdout.rsplit(b"\n", 1)
    head, data = raw.split(b'\r\n\r\n', 1)
    values = dict(line.decode().split(': ', 1) for line in head.split(b'\r\n')[1:] if b': ' in line)
    if response_headers:
        return int(status), data, {k.lower(): v for k, v in values.items()}
    return int(status), data


def login():
    global SESSION
    fields = dict(line.split(': ', 1) for line in Path('/root/hegrounding-access.txt').read_text().splitlines())
    status, _, headers = request('/auth/login', authenticated=False, method='POST',
        headers=('Origin: ' + ORIGIN,), body={'username': fields['Username'], 'password': fields['Password']}, response_headers=True)
    assert status == 200, ('login', status)
    SESSION = headers['set-cookie'].split(';')[0]


def get_json(path):
    status, body = request(path)
    assert status == 200, (path, status)
    return json.loads(body)


def main():
    summary = {}
    for path in ("/", "/api/catalog", "/atlas.html", "/labels/", "/labels/api/atlas"):
        assert request(path, authenticated=False)[0] == 401, path
    summary["unauthenticated"] = "401 for both workspaces"
    assert request('/', authenticated=False, headers=('Accept: text/html',))[0] == 303
    for page in ('/login.html', '/login.js', '/login.css', '/i18n.js', '/i18n.css'):
        assert request(page, authenticated=False)[0] == 200
    login()
    summary['login'] = 'Form session login works; anonymous pages redirect; no Basic Auth prompt'
    for prefix, expected_count in (("", 110), ("/labels", 8)):
        catalog = get_json(prefix + "/api/catalog")
        count = sum(b["total"] for b in catalog["battles"])
        assert count == expected_count, (prefix, count)
        assert catalog["workspace"]["place_lab_url"] == "/labels/place-lab.html"
        for page in ("/", "/atlas.html", "/place-lab.html"):
            status, html = request(prefix + page)
            assert status == 200
            assert f'<base href="{prefix}/">'.encode() in html
        for asset in ("/workspace-url.js", "/atlas-api.js", "/i18n.js", "/i18n.css", "/vendor/leaflet.js", "/vendor/countries.geojson"):
            assert request(prefix + asset)[0] == 200
        atlas = get_json(prefix + "/api/atlas")
        predictions = 0
        places = 0
        for item in atlas["maps"]:
            detail = get_json(prefix + "/api/atlas/" + item["id"])
            if detail['reference_event']:
                assert request(prefix + "/maps/" + detail["reference_event"])[0] == 200
            if item["active"]:
                status, image = request(prefix + "/atlas-assets/" + item["active"]["version"])
                assert status == 200
                assert hashlib.sha256(image).hexdigest() == item["active"]["image_sha256"]
            predictions += sum(len(e["predictions"]) for e in detail["events"])
            lab = get_json(prefix + "/api/atlas/" + item["id"] + "/places")
            places += len(lab["tasks"])
        headers = ("Origin: " + ORIGIN, "X-CSRF-Token: " + catalog["csrf"])
        assert request(prefix + "/api/atlas/test/place-predict", method="POST", headers=headers)[0] == 403
        assert request(prefix + "/api/event/nonexistent", method="POST", headers=headers)[0] == 404
        assert request(prefix + "/api/event/nonexistent", method="POST",
                       headers=("Origin: https://evil.example", "X-CSRF-Token: " + catalog["csrf"]))[0] == 403
        for private in ("/.env", "/.git/config", "/annotation_server.py"):
            assert request(prefix + private)[0] == 404
        data_root = Path("/var/lib/hegrounding") / ("labels" if prefix else "events") / "benchmark/atlas"
        stored = {}
        for name in ("gold.jsonl", "predictions.jsonl", "place_lab/gold.jsonl", "place_lab/predictions.jsonl"):
            path = data_root / name
            stored[name] = sum(bool(line.strip()) for line in path.read_text().splitlines()) if path.exists() else 0
        summary[prefix or "/"] = {"events": count, "maps": len(atlas["maps"]),
                                   "active_event_predictions": predictions, "place_tasks": places,
                                   "stored_history_rows": stored}
    if len(sys.argv) > 1:
        manifest = json.loads(Path(sys.argv[1]).read_text())
        verified = 0
        for relative, expected in manifest.items():
            if relative.startswith("data/"):
                path = Path("/var/lib/hegrounding") / relative.removeprefix("data/")
                assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, relative
                verified += 1
        summary["unchanged_snapshot_files"] = verified
    summary["tls"] = "Certificate verified by curl (no insecure flag)"
    assert request('/auth/logout', method='POST', headers=('Origin: ' + ORIGIN,), body={})[0] == 200
    assert request('/api/catalog')[0] == 401
    summary['logout'] = 'Session revoked; API is protected again'
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
