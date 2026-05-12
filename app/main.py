from fastapi import FastAPI
import uvicorn

from app.core.config import config

app = FastAPI(title="2026-bioimages API")


@app.get("/hello")
def hello_world() -> dict[str, str]:
    return {"message": "Hello, world!"}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=config.app_host,
        port=config.app_port,
        reload=config.app_reload,
    )
