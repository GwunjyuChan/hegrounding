"""Human review journal; public mode requires an authenticated loopback proxy."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import secrets
import sys
import threading
from urllib.parse import unquote, urlsplit


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "benchmark"))
from atlas_store import AtlasStore

DECISIONS = {"accepted", "modified_accepted", "accepted_no_location", "needs_changes", "needs_evidence", "rejected", "pending"}


class Conflict(ValueError):
    pass


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


class ReviewStore:
    def __init__(self, root):
        self.root = Path(root)
        self.source = self.root / "annotations.jsonl"
        raw = self.source.read_bytes()
        self.source_hash = hashlib.sha256(raw).hexdigest()
        self.records = {r["event_id"]: r for r in (json.loads(line) for line in raw.decode().splitlines() if line.strip())}
        self.versions = {eid: digest(r) for eid, r in self.records.items()}
        self.manifest = json.loads((self.root / "manifest.json").read_text(encoding="utf-8"))
        self.journal = self.root / "human_reviews.jsonl"
        self.lock = threading.RLock()

    def assert_current(self):
        if hashlib.sha256(self.source.read_bytes()).hexdigest() != self.source_hash:
            raise Conflict("Candidate data changed. Restart the review server and reload the page.")

    def latest(self, stream):
        stream.seek(0)
        rows = {}
        for line in stream:
            if line.strip():
                record = json.loads(line)
                rows[record["event_id"]] = record
        return rows

    def catalog(self):
        with self.lock:
            self.assert_current()
            reviews = {}
            if self.journal.exists():
                with self.journal.open(encoding="utf-8") as stream:
                    fcntl.flock(stream, fcntl.LOCK_SH)
                    reviews = self.latest(stream)
            return {"round_id": self.manifest["round_id"],
                    "geometry_editing": True,
                    "decisions_sha256": self.manifest["annotation_decisions_sha256"],
                    "candidate_versions": self.versions, "reviews": reviews}

    def save(self, body):
        if not isinstance(body, dict):
            raise ValueError("Expected a JSON object")
        event_id = body.get("event_id")
        if not isinstance(event_id, str) or event_id not in self.records:
            raise ValueError("Unknown event")
        decision = body.get("decision")
        if not isinstance(decision, str) or decision not in DECISIONS:
            raise ValueError("Unknown review decision")
        reviewer, notes = body.get("reviewer", ""), body.get("notes", "")
        if not isinstance(reviewer, str) or not reviewer.strip() or len(reviewer) > 100:
            raise ValueError("Enter a reviewer name (maximum 100 characters).")
        if not isinstance(notes, str) or len(notes) > 10000:
            raise ValueError("Notes must be text, maximum 10,000 characters.")
        source = self.records[event_id]
        if decision in {"modified_accepted", "needs_changes", "needs_evidence", "rejected"} and not notes.strip():
            raise ValueError("Add a reason or the change required in Notes.")
        if decision == "accepted" and source["status"] != "proposed" and not notes.strip():
            raise ValueError("Explain how the candidate's uncertainty was resolved before accepting it.")
        if decision == "accepted_no_location" and source["status"] != "outside_map" and not notes.strip():
            raise ValueError("Explain why the place cannot be marked on this map.")
        revision = body.get("revision")
        if type(revision) is not int or revision < 0:
            raise ValueError("Invalid review revision")
        with self.lock:
            self.assert_current()
            if body.get("candidate_sha256") != self.versions[event_id]:
                raise Conflict("Candidate version changed. Reload before reviewing.")
            with self.journal.open("a+", encoding="utf-8") as stream:
                fcntl.flock(stream, fcntl.LOCK_EX)
                previous = self.latest(stream).get(event_id)
                if revision != (previous["revision"] if previous else 0):
                    raise Conflict("Another tab saved this event. Reload reviews before saving again.")
                # Older clients may update notes but must never silently discard a revision.
                geometry = body.get("human_geometry", previous.get("human_geometry", source["geometry"]) if previous else source["geometry"])
                if "human_geometry" in body and body.get("image_sha256") != source["annotation_image"]["sha256"]:
                    raise Conflict("Annotation image changed. Reload before editing geometry.")
                if geometry is not None:
                    image = source["annotation_image"]
                    geometry = AtlasStore.geometry(geometry, image["width"], image["height"])
                changed = geometry != source["geometry"]
                if decision in {"accepted", "modified_accepted"} and geometry is None:
                    raise ValueError("There is no geometry to accept. Draw a geometry or mark Needs evidence.")
                if decision == "accepted" and changed:
                    raise ValueError("Use Modified & accepted for a changed geometry.")
                # An abstention item: the reviewer confirms the asked place is not on this map, so no geometry is stored.
                if decision == "accepted_no_location" and geometry is not None:
                    raise ValueError("Clear the geometry before confirming the place is not on this map.")
                if decision == "modified_accepted" and not changed:
                    raise ValueError("Geometry is unchanged. Use Accept for the original candidate.")
                record = {"schema_version": 2, "round_id": self.manifest["round_id"],
                          "event_id": event_id, "decision": decision,
                          "reviewer": reviewer.strip(), "notes": notes.strip(),
                          "revision": revision + 1, "reviewed_at": datetime.now(timezone.utc).isoformat(),
                          "candidate_sha256": self.versions[event_id], "candidate_status": source["status"],
                          "annotation_image": source["annotation_image"],
                          "human_geometry": geometry,
                          "geometry_source": "human_edit" if changed else "ai_candidate",
                          "coordinate_system": "native_image_pixels_top_left",
                          "review_kind": "human_review_of_ai_candidate", "eligible_for_scoring": False}
                stream.seek(0, os.SEEK_END)
                stream.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
                return record


class Handler(BaseHTTPRequestHandler):
    def send(self, status, body, mime="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(data)

    def trusted(self):
        if self.server.public_origin:
            return self.headers.get("Host") == urlsplit(self.server.public_origin).netloc
        port = self.server.server_address[1]
        return self.headers.get("Host") in {f"127.0.0.1:{port}", f"localhost:{port}"}

    def do_GET(self):
        if not self.trusted():
            return self.send(403, {"error": "Untrusted review host"})
        path = unquote(urlsplit(self.path).path)
        try:
            if path == "/api/reviews":
                return self.send(200, {**self.server.store.catalog(), "csrf": self.server.token})
            if path == "/api/reviews/export":
                return self.send(200, self.server.store.catalog())
            name = "review.html" if path == "/" else path.lstrip("/")
            allowed = {"review.html", "REPORT.md", "PROTOCOL.md", "annotations.jsonl", "manifest.json", "decisions.json", "browser_validation.json"}
            assets = self.server.store.manifest.get("web_assets", [])
            if name not in allowed and name not in assets and not (name.startswith("overviews/") and name.endswith(".png")):
                return self.send(404, {"error": "Not found"})
            file = (self.server.store.root / name).resolve()
            if not file.is_relative_to(self.server.store.root.resolve()) or not file.is_file():
                return self.send(404, {"error": "Not found"})
            mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
            if file.suffix == ".md":
                mime = "text/plain; charset=utf-8"
            return self.send(200, file.read_bytes(), mime)
        except Conflict as error:
            return self.send(409, {"error": str(error)})
        except (OSError, ValueError):
            return self.send(500, {"error": "Could not read review data; no changes were made."})

    def do_POST(self):
        origin = self.server.public_origin or "http://" + self.headers.get("Host", "")
        if (not self.trusted() or self.headers.get("Origin") != origin
                or not secrets.compare_digest(self.headers.get("X-CSRF-Token", ""), self.server.token)):
            return self.send(403, {"error": "Untrusted local review request"})
        if urlsplit(self.path).path != "/api/reviews":
            return self.send(404, {"error": "Not found"})
        if self.headers.get_content_type() != "application/json":
            return self.send(415, {"error": "Expected application/json"})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 65536:
                return self.send(413, {"error": "Invalid request size"})
            body = json.loads(self.rfile.read(size))
            return self.send(200, {"review": self.server.store.save(body)})
        except Conflict as error:
            return self.send(409, {"error": str(error)})
        except (ValueError, UnicodeError) as error:
            return self.send(400, {"error": str(error)})
        except OSError:
            return self.send(500, {"error": "Review could not be saved. Keep your notes and retry."})


def make_server(root=HERE, port=8771, public_origin=None):
    if public_origin:
        parsed = urlsplit(public_origin)
        if parsed.scheme != "https" or not parsed.netloc or parsed.path or parsed.query or parsed.fragment or parsed.username:
            raise ValueError("Public origin must be an HTTPS origin without a path")
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.public_origin = public_origin
    server.store = ReviewStore(root)
    server.token = secrets.token_hex(32)
    return server


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8771)
    parser.add_argument("--root", type=Path, default=HERE)
    parser.add_argument("--public-origin", help="HTTPS origin behind an authenticated reverse proxy; listener remains loopback-only")
    args = parser.parse_args()
    server = make_server(args.root, args.port, args.public_origin)
    print(f"Human review: http://127.0.0.1:{server.server_address[1]}/review.html", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
