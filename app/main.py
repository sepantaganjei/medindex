from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.api.object_storage import router as object_storage_router
from app.api.radiomics import router as radiomics_router
from app.api.viewer import router as viewer_router
from app.api.get_data import router as get_router
from app.api.add_data import router as add_router
from app.core.config import config

app = FastAPI(title="2026-bioimages API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(config.cors_allow_origins),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(object_storage_router)
app.include_router(radiomics_router)
app.include_router(viewer_router)
app.include_router(get_router)
app.include_router(add_router)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=config.app_host,
        port=config.app_port,
        reload=config.app_reload,
    )
