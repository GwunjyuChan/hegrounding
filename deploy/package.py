"""Build an allowlisted deployment snapshot, without keys, models or the venv."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "benchmark"))
from annotation_server import DATASETS


def copy_file(source, destination):
    source = source.resolve()
    if not source.is_relative_to(ROOT) or source.name.startswith(".env"):
        raise ValueError(f"Unsafe deployment source: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def copy_tree(source, destination):
    for path in source.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"Unexpected symlink: {path}")
        if path.is_file() and not any(p.startswith(".") or p == "__pycache__" for p in path.relative_to(source).parts):
            copy_file(path, destination / path.relative_to(source))


def workspace(source, target):
    for dataset, annotation in DATASETS:
        path = source / dataset
        if path.exists():
            copy_file(path, target / dataset)
            for line in path.read_text().splitlines():
                if line.strip():
                    image = json.loads(line)["image"]
                    if Path(image).is_absolute() or ".." in Path(image).parts:
                        raise ValueError("Unsafe map path")
                    copy_file(source / image, target / image)
        if (source / annotation).exists():
            copy_file(source / annotation, target / annotation)
    copy_tree(source / "benchmark/atlas", target / "benchmark/atlas")


def main():
    target = Path(sys.argv[1]).resolve()
    target.mkdir(parents=True, exist_ok=False)
    for path in (ROOT / "benchmark").glob("*.py"):
        copy_file(path, target / "app/benchmark" / path.name)
    copy_file(ROOT / "benchmark/map_expansion_battles.json", target / "app/benchmark/map_expansion_battles.json")
    copy_tree(ROOT / "benchmark/gui", target / "app/benchmark/gui")
    copy_tree(ROOT / "deploy", target / "app/deploy")
    workspace(ROOT, target / "data/events")
    workspace(ROOT / "benchmark/diagnostics/zurich_labels_20260921/workspace", target / "data/labels")
    files = {str(p.relative_to(target)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in target.rglob("*") if p.is_file()}
    (target / "manifest.json").write_text(json.dumps(files, indent=2) + "\n")
    print(f"Packaged {len(files)} files into {target}")


if __name__ == "__main__":
    main()
