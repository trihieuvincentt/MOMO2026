from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api.routes.cases import router as cases_router
from backend.app.api.routes.message import router as message_router
from backend.app.api.routes.ocr import router as ocr_router
from backend.app.api.routes.links import router as links_router
from backend.app.api.routes.visual import router as visual_router
from backend.app.api.routes.url import router as url_router

app = FastAPI(title="ScamGuard API", version="0.1.0")
app.include_router(message_router)
app.include_router(url_router)
app.include_router(cases_router)
app.include_router(ocr_router)
app.include_router(links_router)
app.include_router(visual_router)

_FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
if _FRONTEND_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=_FRONTEND_DIR), name="static")


@app.get("/")
def frontend() -> FileResponse:
    return FileResponse(_FRONTEND_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
