from pathlib import Path
from typing import Optional

import git

from dataman.metadata import read_metadata


def list_datasets_from_repo(repo_path: Path) -> list[dict]:
    repo = git.Repo(repo_path)
    results = []
    for tag in repo.tags:
        if not tag.name.startswith("dataset/"):
            continue
        parts = tag.name.split("/")
        if len(parts) != 3:
            continue
        _, name, version_str = parts
        results.append({
            "snapshot_id": tag.name,
            "name": name,
            "version": version_str.lstrip("v"),
        })
    return sorted(results, key=lambda d: d["snapshot_id"])


def get_dataset_detail(snapshot_id: str, nfs_dataset_paths: list[Path]) -> Optional[dict]:
    """Search all NFS dataset directories for the given snapshot_id."""
    parts = snapshot_id.split("/")
    if len(parts) != 3:
        return None
    _, name, version_str = parts
    version = version_str.lstrip("v")
    prefix = f"{name}_v{version}_"
    for nfs_datasets in nfs_dataset_paths:
        if not nfs_datasets.exists():
            continue
        for candidate in nfs_datasets.iterdir():
            if candidate.is_dir() and candidate.name.startswith(prefix):
                try:
                    return read_metadata(candidate)
                except FileNotFoundError:
                    continue
    return None
