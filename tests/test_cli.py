import json
import pytest
import git as gitlib
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from pathlib import Path
from PIL import Image
from dataman.cli import cli

runner = CliRunner()


def _make_dataset(tmp_path) -> Path:
    Image.new("RGB", (640, 480)).save(tmp_path / "frame_0001.jpg")
    meta = {
        "name": "pedestrian", "version": "2.0",
        "snapshot_id": "dataset/pedestrian/v2.0",
        "registered_by": "austin", "registered_on": "2026-06-01",
        "file_count": 1, "total_size_bytes": 500,
        "quality_score": 100.0, "quality_issues": [],
    }
    (tmp_path / "metadata.json").write_text(json.dumps(meta))
    return tmp_path


def test_scan_command_exits_zero(tmp_path):
    _make_dataset(tmp_path)
    result = runner.invoke(cli, ["scan", "--path", str(tmp_path)])
    assert result.exit_code == 0
    assert "quality_score" in result.output



def test_info_command_shows_metadata(tmp_path):
    _make_dataset(tmp_path)
    result = runner.invoke(cli, ["info", "--path", str(tmp_path)])
    assert result.exit_code == 0
    assert "pedestrian" in result.output
    assert "100.0" in result.output


def test_register_command_validates_name(tmp_path):
    _make_dataset(tmp_path)
    result = runner.invoke(cli, [
        "register", "--path", str(tmp_path),
        "--name", "Bad Name", "--version", "2.0"
    ])
    assert result.exit_code != 0


def test_pull_command(tmp_path):
    from dataman.nfs_config import NfsConfig
    repo = gitlib.Repo.init(tmp_path)
    repo.config_writer().set_value("user", "name", "T").release()
    repo.config_writer().set_value("user", "email", "t@t.com").release()
    (tmp_path / "README.md").write_text("x")
    repo.index.add(["README.md"])
    repo.index.commit("init")
    repo.create_tag("dataset/pedestrian/v2.0")
    fake_cfg = NfsConfig(
        default_remote="nfs-1",
        remotes={"nfs-1": "/mnt/nfs1/dvc-remote"},
        routing={"pedestrian": "nfs-1"},
    )
    with patch("dataman.nfs_config.load_nfs_config", return_value=fake_cfg), \
         patch("dataman.cli.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        result = runner.invoke(cli, ["pull", "dataset/pedestrian/v2.0",
                                     "--repo-path", str(tmp_path)])
    assert result.exit_code == 0
    assert "pulled successfully" in result.output
