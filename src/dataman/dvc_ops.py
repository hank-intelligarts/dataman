import hashlib
import subprocess
import yaml
from pathlib import Path


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(cwd) if cwd else None)
    if result.returncode != 0:
        raise RuntimeError(f"{cmd[0]} {cmd[1]} failed: {result.stderr.strip()}")


def dvc_add(path: Path, repo_path: Path | None = None) -> None:
    cwd = repo_path or path.parent
    if repo_path and not str(path).startswith(str(repo_path)):
        # External path: write .dvc file manually (DVC 3.x doesn't support symlinks)
        _write_external_dvc_file(path, repo_path)
    else:
        _run(["dvc", "add", str(path)], cwd=cwd)


def _write_external_dvc_file(path: Path, repo_path: Path) -> None:
    dvc_file = repo_path / (path.name + ".dvc")
    out = {"path": str(path)}
    if path.is_dir():
        out["md5"] = _dir_md5(path)
    else:
        out["md5"] = hashlib.md5(path.read_bytes()).hexdigest()
    content = {"outs": [out]}
    dvc_file.write_text(yaml.dump(content, default_flow_style=False))


def _dir_md5(path: Path) -> str:
    h = hashlib.md5()
    for f in sorted(path.rglob("*")):
        if f.is_file():
            h.update(f.read_bytes())
    return h.hexdigest()


def dvc_push(remote: str, repo_path: Path | None = None) -> None:
    _run(["dvc", "push", "-r", remote], cwd=repo_path)


def dvc_pull(path: Path, remote: str) -> None:
    _run(["dvc", "pull", "-r", remote, str(path)])
