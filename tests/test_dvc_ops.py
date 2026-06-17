import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from dataman.dvc_ops import dvc_add, dvc_push, dvc_pull


def test_dvc_add_calls_subprocess(tmp_path):
    with patch("dataman.dvc_ops.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        dvc_add(tmp_path)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "dvc"
        assert args[1] == "add"
        assert str(tmp_path) in args


def test_dvc_push_calls_subprocess_with_remote():
    with patch("dataman.dvc_ops.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        dvc_push(remote="nfs-1")
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[:4] == ["dvc", "push", "-r", "nfs-1"]


def test_dvc_pull_calls_subprocess_with_remote(tmp_path):
    with patch("dataman.dvc_ops.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        dvc_pull(tmp_path, remote="nfs-2")
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "-r" in args
        assert "nfs-2" in args


def test_dvc_add_raises_on_failure(tmp_path):
    with patch("dataman.dvc_ops.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=1, stderr="error")
        with pytest.raises(RuntimeError, match="dvc add failed"):
            dvc_add(tmp_path)
