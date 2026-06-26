import subprocess
from pathlib import Path


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd) if cwd else None)
    if result.returncode != 0:
        raise RuntimeError(f"{cmd[0]} {cmd[1]} failed: {result.stderr.strip()}")


def dvc_add(path: Path, repo_path: Path | None = None) -> None:
    # DVC 3.x requires data to be inside the project, use symlink if external
    if repo_path and not str(path).startswith(str(repo_path)):
        link = repo_path / path.name
        if not link.exists():
            link.symlink_to(path)
        _run(["dvc", "add", path.name], cwd=repo_path)
    else:
        _run(["dvc", "add", str(path)])


def dvc_push(remote: str) -> None:
    _run(["dvc", "push", "-r", remote])


def dvc_pull(path: Path, remote: str) -> None:
    _run(["dvc", "pull", "-r", remote, str(path)])
