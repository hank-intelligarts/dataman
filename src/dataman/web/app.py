from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from dataman.web.routes import router

_STATIC = Path(__file__).parent / "static"


def create_app(repo_path: Path, nfs_dataset_paths: list[Path]) -> FastAPI:
    app = FastAPI(title="dataman Web UI")
    app.state.repo_path = repo_path
    app.state.nfs_dataset_paths = nfs_dataset_paths
    app.include_router(router)
    app.mount("/", StaticFiles(directory=_STATIC, html=True), name="static")
    return app
