import pytest
from pathlib import Path
from dataman.nfs_config import load_nfs_config, resolve_remote, get_remote_path, NfsConfig

SAMPLE_TOML = """\
[nfs]
default = "nfs-1"

[nfs.remotes]
nfs-1 = "/mnt/nfs1/dvc-remote"
nfs-2 = "/mnt/nfs2/dvc-remote"

[nfs.routing]
pedestrian = "nfs-1"
drone = "nfs-2"
"""


@pytest.fixture
def config_file(tmp_path):
    f = tmp_path / "config.toml"
    f.write_text(SAMPLE_TOML)
    return f


def test_load_nfs_config(config_file):
    cfg = load_nfs_config(config_file)
    assert cfg.default_remote == "nfs-1"
    assert cfg.remotes["nfs-1"] == "/mnt/nfs1/dvc-remote"
    assert cfg.remotes["nfs-2"] == "/mnt/nfs2/dvc-remote"
    assert cfg.routing["drone"] == "nfs-2"


def test_load_nfs_config_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="dataman config not found"):
        load_nfs_config(tmp_path / "nonexistent.toml")


def test_resolve_remote_exact_match(config_file):
    cfg = load_nfs_config(config_file)
    assert resolve_remote("drone", cfg) == "nfs-2"
    assert resolve_remote("pedestrian", cfg) == "nfs-1"


def test_resolve_remote_fallback_to_default(config_file):
    cfg = load_nfs_config(config_file)
    assert resolve_remote("cars", cfg) == "nfs-1"  # not in routing, uses default


def test_get_remote_path(config_file):
    cfg = load_nfs_config(config_file)
    assert get_remote_path("nfs-2", cfg) == Path("/mnt/nfs2/dvc-remote")


def test_get_remote_path_unknown(config_file):
    cfg = load_nfs_config(config_file)
    with pytest.raises(ValueError, match="not found in config"):
        get_remote_path("nfs-99", cfg)
