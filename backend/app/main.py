from fastapi import FastAPI

from backend.app.api.routes.message import router as message_router

app = FastAPI(title="ScamGuard API", version="0.1.0")
app.include_router(message_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
