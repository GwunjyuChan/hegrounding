"""Build a minimal review deployment, without credentials or model artifacts."""
import argparse
import fcntl
import importlib.util
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
ROUND = Path("benchmark/annotations/assistant_round_20261011")


def package(destination):
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=False)
    source = ROOT / ROUND
    sys.path.insert(0, str(source))
    spec = importlib.util.spec_from_file_location("review_build", source / "build.py")
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    data = destination / "data"
    data.mkdir()
    records = [json.loads(line) for line in (source / "annotations.jsonl").read_text().splitlines() if line.strip()]
    manifest = json.loads((source / "manifest.json").read_text())
    assets = {m["path"]: m for m in manifest["image_assets"]}
    manifest["web_assets"] = sorted({f"images/{m['sha256']}{Path(m['path']).suffix}" for m in assets.values()})
    build.render_review(records, manifest, assets, web_root=data)
    (data / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    for name in ["annotations.jsonl", "decisions.json", "REPORT.md", "PROTOCOL.md"]:
        shutil.copy2(source / name, data / name)
    with (source / "human_reviews.jsonl").open("rb") as journal:
        fcntl.flock(journal, fcntl.LOCK_SH)
        (data / "human_reviews.jsonl").write_bytes(journal.read())
    for relative in [ROUND / "serve_reviews.py", Path("benchmark/atlas_store.py"),
                     Path("benchmark/annotate_geo.py"), Path("deploy/install_reviews.py")]:
        target = destination / "app" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    print(destination)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    package(parser.parse_args().destination)
