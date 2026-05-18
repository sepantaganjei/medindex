from fastapi import APIRouter

router = APIRouter(tags=["example"])


@router.get("/hello")
def hello_world() -> dict[str, str]:
    return {"message": "Hello, world!"}
