from fastapi import FastAPI

from backend.app.api.routes.cases import router as cases_router
from backend.app.api.routes.message import router as message_router
from backend.app.api.routes.ocr import router as ocr_router
from backend.app.api.routes.url import router as url_router

app = FastAPI(title="ScamGuard API", version="0.1.0")
app.include_router(message_router)
app.include_router(url_router)
app.include_router(cases_router)
app.include_router(ocr_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
