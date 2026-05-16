from fastapi import FastAPI
import uvicorn

from app.api.example import router as example_router
from app.api.mock import router as mock_router
from app.core.config import config

app = FastAPI(title="2026-bioimages API")
app.include_router(example_router)
app.include_router(mock_router)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=config.app_host,
        port=config.app_port,
        reload=config.app_reload,
    )
