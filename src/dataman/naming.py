import re

_NAME_RE = re.compile(r"^[a-z0-9_]+$")
_VERSION_RE = re.compile(r"^\d+\.\d+$")


def validate_name(name: str) -> None:
    if not _NAME_RE.match(name):
        raise ValueError(
            f"Dataset name must be lowercase alphanumeric/underscore, got: {name!r}"
        )


def validate_version(version: str) -> None:
    if not _VERSION_RE.match(version):
        raise ValueError(
            f"Version must be numeric like '2.0', got: {version!r}"
        )


def dataset_dir_name(name: str, version: str, date_str: str) -> str:
    return f"{name}_v{version}_{date_str}"


def snapshot_tag(name: str, version: str) -> str:
    return f"dataset/{name}/v{version}"
