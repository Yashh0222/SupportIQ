"""User endpoint for requesting origin approval."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import require_auth
from app.origin_requests import create_request, list_requests_for_user
from app.models.schemas import OriginApprovalRequest

router = APIRouter(tags=["origin-requests"])


@router.get("/origin-requests/mine")
def my_origin_requests(payload: dict = Depends(require_auth)) -> list[dict]:
    """Return all origin requests made by the current user."""
    user_id = payload.get("sub", "")
    requests = list_requests_for_user(user_id)
    return [
        {
            "id": r.id,
            "origin": r.origin,
            "company_id": r.company_id,
            "reason": r.reason,
            "status": r.status,
            "created_at": r.created_at,
        }
        for r in requests
    ]


@router.post("/origin-requests", status_code=201)
def submit_origin_request(
    req: OriginApprovalRequest,
    payload: dict = Depends(require_auth),
) -> dict:
    """Any authenticated user can submit an origin approval request."""
    user_id = payload.get("sub", "")
    user_email = payload.get("email", "")

    request_id = f"or_{uuid.uuid4().hex[:12]}"
    origin_req = create_request(
        request_id=request_id,
        user_id=user_id,
        user_email=user_email,
        company_id=req.company_id,
        origin=req.origin,
        reason=req.reason,
    )
    return {
        "id": origin_req.id,
        "origin": origin_req.origin,
        "company_id": origin_req.company_id,
        "status": origin_req.status,
        "message": "Your origin request has been submitted. An admin will review it shortly.",
    }
