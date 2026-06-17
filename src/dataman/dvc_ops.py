import subprocess
from pathlib import Path


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"{cmd[0]} {cmd[1]} failed: {result.stderr.strip()}")


def dvc_add(path: Path) -> None:
    _run(["dvc", "add", str(path)])


def dvc_push(remote: str) -> None:
    _run(["dvc", "push", "-r", remote])


def dvc_pull(path: Path, remote: str) -> None:
    _run(["dvc", "pull", "-r", remote, str(path)])
