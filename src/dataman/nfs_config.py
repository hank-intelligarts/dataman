from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore


CONFIG_PATH = Path.home() / ".dataman" / "config.toml"


@dataclass
class NfsConfig:
    default_remote: str
    remotes: dict[str, str]  # remote_name → dvc cache path
    routing: dict[str, str]  # dataset_name → remote_name
    _raw_remotes: dict = field(default_factory=dict)


def load_nfs_config(config_path: Path = CONFIG_PATH) -> NfsConfig:
    if not config_path.exists():
        raise FileNotFoundError(
            f"dataman config not found at {config_path}. "
            "Run 'dataman config init' to create it."
        )
    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    nfs = data.get("nfs", {})
    raw_remotes = nfs.get("remotes", {})
    # Support both old format (str) and new format (dict with cache/datasets)
    remotes = {}
    for name, val in raw_remotes.items():
        if isinstance(val, dict):
            remotes[name] = val.get("cache", "")
        else:
            remotes[name] = val
    return NfsConfig(
        default_remote=nfs.get("default", ""),
        remotes=remotes,
        routing=nfs.get("routing", {}),
        _raw_remotes=raw_remotes,
    )


def resolve_remote(name: str, config: NfsConfig) -> str:
    """Return DVC remote name for a dataset name. Falls back to default."""
    if name in config.routing:
        return config.routing[name]
    if config.default_remote:
        return config.default_remote
    raise ValueError(
        f"No NFS remote found for dataset '{name}' and no default configured."
    )


def get_remote_path(remote_name: str, config: NfsConfig) -> Path:
    """Return the NFS mount path for a DVC remote name."""
    if remote_name not in config.remotes:
        raise ValueError(
            f"NFS remote '{remote_name}' not found in config. "
            f"Available: {list(config.remotes.keys())}"
        )
    return Path(config.remotes[remote_name])


def get_all_dataset_paths(config: NfsConfig) -> list[Path]:
    """Return all NFS dataset directories (one per remote)."""
    paths = []
    for name, val in config._raw_remotes.items():
        if isinstance(val, dict) and "datasets" in val:
            paths.append(Path(val["datasets"]))
        else:
            # Old format: derive from cache path parent
            paths.append(Path(config.remotes[name]).parent / "datasets")
    return paths
