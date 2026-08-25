"""Admin endpoints managing which site origins may access the API."""

from fastapi import APIRouter, Depends, HTTPException

from app.auth import require_admin
from app.models.schemas import AllowedOriginRequest
from app.origins import add_origin, list_origins, remove_origin
from app.origin_requests import list_requests, resolve_request

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


@router.get("/admin/origin-requests")
def get_all_origin_requests(
    status: str | None = None,
    _admin: dict = Depends(require_admin),
) -> list[dict]:
    """Admin-only: list all origin approval requests, optionally filtered by status."""
    requests = list_requests(status=status)
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "user_email": r.user_email,
            "company_id": r.company_id,
            "origin": r.origin,
            "reason": r.reason,
            "status": r.status,
            "created_at": r.created_at,
            "resolved_at": r.resolved_at,
        }
        for r in requests
    ]


@router.post("/admin/origin-requests/{request_id}/approve")
def approve_origin_request(
    request_id: str,
    _admin: dict = Depends(require_admin),
) -> dict:
    """Admin-only: approve an origin request and add the origin to the allowed list."""
    req = resolve_request(request_id, "approved")
    if req is None:
        raise HTTPException(status_code=404, detail="Request not found.")

    # Also add the origin to the allowed list
    try:
        add_origin(req.origin)
    except ValueError:
        pass  # Origin might already exist

    return {
        "id": req.id,
        "origin": req.origin,
        "status": req.status,
        "message": f"Origin '{req.origin}' has been approved and added to allowed list.",
    }


@router.post("/admin/origin-requests/{request_id}/reject")
def reject_origin_request(
    request_id: str,
    _admin: dict = Depends(require_admin),
) -> dict:
    """Admin-only: reject an origin request."""
    req = resolve_request(request_id, "rejected")
    if req is None:
        raise HTTPException(status_code=404, detail="Request not found.")
    return {
        "id": req.id,
        "origin": req.origin,
        "status": req.status,
        "message": f"Origin '{req.origin}' request has been rejected.",
    }
