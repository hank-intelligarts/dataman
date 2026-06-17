from pathlib import Path
from typing import List

import git


def commit_and_tag(
    repo_path: Path,
    files_to_add: List[str],
    message: str,
    tag: str,
) -> None:
    repo = git.Repo(repo_path)
    repo.index.add(files_to_add)
    repo.index.commit(message)
    repo.create_tag(tag, message=message)


def push_tags(repo_path: Path) -> None:
    repo = git.Repo(repo_path)
    origin = repo.remote("origin")
    origin.push()
    origin.push(tags=True)


def get_all_tags(repo_path: Path) -> List[str]:
    repo = git.Repo(repo_path)
    return [t.name for t in repo.tags if t.name.startswith("dataset/")]
