"""Admin endpoints managing which site origins may access the API."""

from fastapi import APIRouter, HTTPException

from app.models.schemas import AllowedOriginRequest
from app.origins import add_origin, list_origins, remove_origin

router = APIRouter(tags=["origins"])


@router.get("/origins")
def get_origins() -> dict:
    return {"origins": list_origins()}


@router.post("/origins", status_code=201)
def post_origin(req: AllowedOriginRequest) -> dict:
    try:
        origins = add_origin(req.origin)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"origins": origins}


@router.delete("/origins/{origin:path}")
def delete_origin(origin: str) -> dict:
    return {"origins": remove_origin(origin)}
