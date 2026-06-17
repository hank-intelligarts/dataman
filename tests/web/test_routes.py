import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from dataman.web.app import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(
        repo_path=tmp_path,
        nfs_dataset_paths=[tmp_path / "nfs1" / "datasets", tmp_path / "nfs2" / "datasets"],
    )
    return TestClient(app)


def test_list_endpoint_returns_json(client):
    with patch("dataman.web.routes.list_datasets_from_repo") as mock_list:
        mock_list.return_value = [
            {"snapshot_id": "dataset/pedestrian/v2.0", "name": "pedestrian", "version": "2.0"}
        ]
        resp = client.get("/api/datasets")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert data[0]["snapshot_id"] == "dataset/pedestrian/v2.0"


def test_detail_endpoint_returns_metadata(client):
    meta = {
        "name": "pedestrian", "version": "2.0",
        "snapshot_id": "dataset/pedestrian/v2.0",
        "registered_by": "austin", "registered_on": "2026-06-01",
        "file_count": 5, "total_size_bytes": 1024,
        "quality_score": 98.5, "nfs_remote": "nfs-1", "quality_issues": [],
    }
    with patch("dataman.web.routes.get_dataset_detail") as mock_detail:
        mock_detail.return_value = meta
        resp = client.get("/api/datasets/dataset/pedestrian/v2.0")
    assert resp.status_code == 200
    assert resp.json()["quality_score"] == 98.5
    assert resp.json()["nfs_remote"] == "nfs-1"


def test_detail_endpoint_returns_404_when_not_found(client):
    with patch("dataman.web.routes.get_dataset_detail") as mock_detail:
        mock_detail.return_value = None
        resp = client.get("/api/datasets/dataset/missing/v1.0")
    assert resp.status_code == 404
