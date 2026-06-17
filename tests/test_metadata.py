import json
import pytest
from pathlib import Path
from dataman.metadata import write_metadata, read_metadata, write_manifest


def test_write_metadata_creates_file(tmp_path):
    meta = {
        "name": "pedestrian", "version": "2.0",
        "snapshot_id": "dataset/pedestrian/v2.0",
        "registered_by": "austin", "registered_on": "2026-06-01",
        "file_count": 3, "total_size_bytes": 1024,
        "quality_score": 100.0, "quality_issues": [],
    }
    write_metadata(tmp_path, meta)
    assert (tmp_path / "metadata.json").exists()


def test_write_metadata_roundtrip(tmp_path):
    meta = {
        "name": "pedestrian", "version": "2.0",
        "snapshot_id": "dataset/pedestrian/v2.0",
        "registered_by": "austin", "registered_on": "2026-06-01",
        "file_count": 3, "total_size_bytes": 1024,
        "quality_score": 100.0, "quality_issues": [],
    }
    write_metadata(tmp_path, meta)
    loaded = read_metadata(tmp_path)
    assert loaded["name"] == "pedestrian"
    assert loaded["quality_score"] == 100.0


def test_write_manifest_lists_all_files(tmp_path):
    (tmp_path / "a.jpg").write_bytes(b"fake")
    (tmp_path / "b.jpg").write_bytes(b"fake2")
    write_manifest(tmp_path)
    manifest = (tmp_path / "manifest.txt").read_text()
    assert "a.jpg" in manifest
    assert "b.jpg" in manifest


def test_read_metadata_raises_if_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_metadata(tmp_path)
