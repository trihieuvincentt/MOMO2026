from fastapi import FastAPI

app = FastAPI(title="ScamGuard API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
