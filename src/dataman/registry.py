from dataclasses import dataclass
from datetime import date
from pathlib import Path

from dataman.dvc_ops import dvc_add, dvc_push
from dataman.git_ops import commit_and_tag, push_tags
from dataman.metadata import write_metadata, write_manifest
from dataman.naming import validate_name, validate_version, snapshot_tag
from dataman.scanner import scan_dataset


@dataclass
class RegistrationResult:
    snapshot_id: str
    quality_score: float
    file_count: int
    issue_count: int


def register_dataset(
    path: Path,
    name: str,
    version: str,
    registered_by: str,
    repo_path: Path,
    nfs_remote: str,
) -> RegistrationResult:
    validate_name(name)
    validate_version(version)

    scan = scan_dataset(path)
    tag = snapshot_tag(name, version)
    today = date.today().isoformat()

    meta = {
        "name": name,
        "version": version,
        "snapshot_id": tag,
        "registered_by": registered_by,
        "registered_on": today,
        "file_count": scan.file_count,
        "total_size_bytes": scan.total_size_bytes,
        "quality_score": scan.quality_score,
        "nfs_remote": nfs_remote,
        "quality_issues": [
            {"kind": i.kind, "file": i.file, "detail": i.detail}
            for i in scan.issues
        ],
    }
    write_metadata(path, meta)
    write_manifest(path)

    dvc_add(path, repo_path=repo_path)
    dvc_push(remote=nfs_remote)
    link = repo_path / path.name
    dvc_file = (link if link.exists() and link.is_symlink() else path).name + ".dvc"
    commit_and_tag(
        repo_path=repo_path,
        files_to_add=[dvc_file],
        message=f"register dataset {name} v{version}",
        tag=tag,
    )
    push_tags(repo_path)

    return RegistrationResult(
        snapshot_id=tag,
        quality_score=scan.quality_score,
        file_count=scan.file_count,
        issue_count=len(scan.issues),
    )
