import json
import pytest
import git
from pathlib import Path
from dataman.web.reader import list_datasets_from_repo, get_dataset_detail


def _init_repo_with_datasets(tmp_path) -> Path:
    repo = git.Repo.init(tmp_path)
    repo.config_writer().set_value("user", "name", "T").release()
    repo.config_writer().set_value("user", "email", "t@t.com").release()
    (tmp_path / "README.md").write_text("init")
    repo.index.add(["README.md"])
    repo.index.commit("init")
    repo.create_tag("dataset/pedestrian/v2.0")
    repo.create_tag("dataset/cars/v1.0")
    return tmp_path


def test_list_datasets_returns_all_snapshot_ids(tmp_path):
    repo_path = _init_repo_with_datasets(tmp_path)
    datasets = list_datasets_from_repo(repo_path)
    names = [d["snapshot_id"] for d in datasets]
    assert "dataset/pedestrian/v2.0" in names
    assert "dataset/cars/v1.0" in names


def test_get_dataset_detail_reads_metadata_from_correct_nfs(tmp_path):
    # pedestrian is on nfs-1, drone is on nfs-2
    nfs1_datasets = tmp_path / "nfs1" / "datasets"
    nfs2_datasets = tmp_path / "nfs2" / "datasets"
    nfs1_datasets.mkdir(parents=True)
    nfs2_datasets.mkdir(parents=True)

    dataset_dir = nfs1_datasets / "pedestrian_v2.0_20260601"
    dataset_dir.mkdir(parents=True)
    meta = {
        "name": "pedestrian", "version": "2.0",
        "snapshot_id": "dataset/pedestrian/v2.0",
        "registered_by": "austin", "registered_on": "2026-06-01",
        "file_count": 5, "total_size_bytes": 1024,
        "quality_score": 98.5, "nfs_remote": "nfs-1", "quality_issues": [],
    }
    (dataset_dir / "metadata.json").write_text(json.dumps(meta))

    detail = get_dataset_detail(
        "dataset/pedestrian/v2.0",
        [nfs1_datasets, nfs2_datasets],
    )
    assert detail["quality_score"] == 98.5
    assert detail["nfs_remote"] == "nfs-1"


def test_get_dataset_detail_returns_none_if_not_found(tmp_path):
    nfs_datasets = tmp_path / "datasets"
    nfs_datasets.mkdir()
    detail = get_dataset_detail("dataset/nonexistent/v1.0", [nfs_datasets])
    assert detail is None
