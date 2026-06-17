import hashlib
import json
from pathlib import Path


def write_metadata(dataset_path: Path, meta: dict) -> None:
    (dataset_path / "metadata.json").write_text(json.dumps(meta, indent=2))


def read_metadata(dataset_path: Path) -> dict:
    path = dataset_path / "metadata.json"
    if not path.exists():
        raise FileNotFoundError(f"metadata.json not found in {dataset_path}")
    return json.loads(path.read_text())


def write_manifest(dataset_path: Path) -> None:
    lines = []
    for f in sorted(dataset_path.rglob("*")):
        if f.is_file() and f.name not in {"metadata.json", "manifest.txt"}:
            digest = hashlib.sha256(f.read_bytes()).hexdigest()
            lines.append(f"{digest}  {f.relative_to(dataset_path)}")
    (dataset_path / "manifest.txt").write_text("\n".join(lines) + "\n")
