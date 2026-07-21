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


def find_dataset_path(snapshot_id: str, nfs_dataset_paths: list[Path]) -> Optional[Path]:
    """Return the NFS directory Path for a given snapshot_id, or None."""
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
            if not candidate.is_dir():
                continue
            if candidate.name.lower().startswith(prefix.lower()) or candidate.name.lower() == name.lower():
                try:
                    meta = read_metadata(candidate)
                    if meta.get("snapshot_id") == snapshot_id:
                        return candidate
                except FileNotFoundError:
                    continue
    return None


def get_dataset_detail(snapshot_id: str, nfs_dataset_paths: list[Path]) -> Optional[dict]:
    """Search all NFS dataset directories for the given snapshot_id."""
    path = find_dataset_path(snapshot_id, nfs_dataset_paths)
    if path is None:
        return None
    try:
        return read_metadata(path)
    except FileNotFoundError:
        return None
