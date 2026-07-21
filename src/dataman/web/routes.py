from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from dataman.web.reader import list_datasets_from_repo, get_dataset_detail, find_dataset_path

router = APIRouter()

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}


@router.get("/api/datasets")
def list_datasets(request: Request):
    repo_path: Path = request.app.state.repo_path
    return list_datasets_from_repo(repo_path)


@router.get("/api/datasets/{snapshot_id:path}/files")
def dataset_files(snapshot_id: str, request: Request, dir: str = ""):
    nfs_dataset_paths: list[Path] = request.app.state.nfs_dataset_paths
    base = find_dataset_path(snapshot_id, nfs_dataset_paths)
    if base is None:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {snapshot_id}")

    target = base / dir if dir else base
    target = target.resolve()
    # Safety: must stay inside base
    try:
        target.relative_to(base.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path")

    if not target.exists():
        raise HTTPException(status_code=404, detail="Path not found")

    entries = []
    for p in sorted(target.iterdir()):
        if p.name in {"metadata.json", "manifest.txt"}:
            continue
        rel = str(p.relative_to(base))
        if p.is_dir():
            entries.append({"name": p.name, "type": "dir", "path": rel})
        else:
            is_image = p.suffix.lower() in IMAGE_SUFFIXES
            entries.append({
                "name": p.name,
                "type": "image" if is_image else "file",
                "path": rel,
                "size": p.stat().st_size,
            })
    return {"snapshot_id": snapshot_id, "dir": dir, "entries": entries}


@router.get("/api/datasets/{snapshot_id:path}/preview")
def dataset_preview(snapshot_id: str, request: Request, path: str = ""):
    nfs_dataset_paths: list[Path] = request.app.state.nfs_dataset_paths
    base = find_dataset_path(snapshot_id, nfs_dataset_paths)
    if base is None:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {snapshot_id}")

    file_path = (base / path).resolve()
    try:
        file_path.relative_to(base.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path")

    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    if file_path.suffix.lower() not in IMAGE_SUFFIXES:
        raise HTTPException(status_code=400, detail="Not an image")

    return FileResponse(file_path)


@router.get("/api/datasets/{snapshot_id:path}")
def dataset_detail(snapshot_id: str, request: Request):
    nfs_dataset_paths: list[Path] = request.app.state.nfs_dataset_paths
    meta = get_dataset_detail(snapshot_id, nfs_dataset_paths)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {snapshot_id}")
    return meta
