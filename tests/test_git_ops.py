import pytest
import git
from dataman.git_ops import commit_and_tag, get_all_tags


def _init_repo(tmp_path):
    repo = git.Repo.init(tmp_path)
    repo.config_writer().set_value("user", "name", "Test User").release()
    repo.config_writer().set_value("user", "email", "test@test.com").release()
    (tmp_path / "README.md").write_text("init")
    repo.index.add(["README.md"])
    repo.index.commit("initial commit")
    return repo


def test_commit_and_tag_creates_tag(tmp_path):
    repo = _init_repo(tmp_path)
    (tmp_path / "test.dvc").write_text("oid sha256:abc\nsize 100\n")
    commit_and_tag(
        repo_path=tmp_path,
        files_to_add=["test.dvc"],
        message="register pedestrian v2.0",
        tag="dataset/pedestrian/v2.0",
    )
    assert "dataset/pedestrian/v2.0" in [t.name for t in repo.tags]


def test_get_all_tags_returns_dataset_tags(tmp_path):
    repo = _init_repo(tmp_path)
    repo.create_tag("dataset/pedestrian/v1.0")
    repo.create_tag("dataset/cars/v3.0")
    repo.create_tag("unrelated-tag")
    tags = get_all_tags(tmp_path)
    assert "dataset/pedestrian/v1.0" in tags
    assert "dataset/cars/v3.0" in tags
    assert "unrelated-tag" not in tags
