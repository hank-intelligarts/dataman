from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

from dataman.web.reader import list_datasets_from_repo, get_dataset_detail

router = APIRouter()


@router.get("/api/datasets")
def list_datasets(request: Request):
    repo_path: Path = request.app.state.repo_path
    return list_datasets_from_repo(repo_path)


@router.get("/api/datasets/{snapshot_id:path}")
def dataset_detail(snapshot_id: str, request: Request):
    nfs_dataset_paths: list[Path] = request.app.state.nfs_dataset_paths
    meta = get_dataset_detail(snapshot_id, nfs_dataset_paths)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {snapshot_id}")
    return meta
