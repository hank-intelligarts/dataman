import pytest
from unittest.mock import patch
from pathlib import Path
from PIL import Image
from dataman.registry import register_dataset, RegistrationResult


def _make_valid_dataset(tmp_path) -> Path:
    d = tmp_path / "pedestrian_v2.0_20260601"
    d.mkdir(parents=True)
    Image.new("RGB", (640, 480)).save(d / "frame_0001.jpg")
    return d


def test_register_returns_result(tmp_path):
    dataset_path = _make_valid_dataset(tmp_path)
    with patch("dataman.registry.dvc_add"), \
         patch("dataman.registry.dvc_push"), \
         patch("dataman.registry.commit_and_tag"), \
         patch("dataman.registry.push_tags"):
        result = register_dataset(
            path=dataset_path,
            name="pedestrian",
            version="2.0",
            registered_by="austin",
            repo_path=tmp_path,
            nfs_remote="nfs-1",
        )
    assert isinstance(result, RegistrationResult)
    assert result.snapshot_id == "dataset/pedestrian/v2.0"
    assert result.quality_score == 100.0


def test_register_writes_metadata_with_nfs_remote(tmp_path):
    import json
    dataset_path = _make_valid_dataset(tmp_path)
    with patch("dataman.registry.dvc_add"), \
         patch("dataman.registry.dvc_push"), \
         patch("dataman.registry.commit_and_tag"), \
         patch("dataman.registry.push_tags"):
        register_dataset(
            path=dataset_path,
            name="pedestrian",
            version="2.0",
            registered_by="austin",
            repo_path=tmp_path,
            nfs_remote="nfs-1",
        )
    assert (dataset_path / "metadata.json").exists()
    assert (dataset_path / "manifest.txt").exists()
    meta = json.loads((dataset_path / "metadata.json").read_text())
    assert meta["nfs_remote"] == "nfs-1"


def test_register_raises_on_invalid_name(tmp_path):
    dataset_path = _make_valid_dataset(tmp_path)
    with pytest.raises(ValueError, match="lowercase alphanumeric"):
        register_dataset(
            path=dataset_path,
            name="My Dataset",
            version="2.0",
            registered_by="austin",
            repo_path=tmp_path,
            nfs_remote="nfs-1",
        )
