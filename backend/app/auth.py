"""Clerk authentication dependencies for FastAPI routes."""

import os
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from clerk_backend_api import Clerk
from clerk_backend_api.security import authenticate_request
from clerk_backend_api.security.types import AuthenticateRequestOptions

CLERK_SECRET_KEY = os.environ.get("CLERK_SECRET_KEY", "")
CLERK_AUTHORIZED_PARTIES = [
    p.strip()
    for p in os.environ.get("CLERK_AUTHORIZED_PARTIES", "http://localhost:5173").split(",")
    if p.strip()
]

clerk_client = Clerk(bearer_auth=CLERK_SECRET_KEY) if CLERK_SECRET_KEY else None


def _get_clerk_client() -> Clerk:
    if clerk_client is None:
        raise HTTPException(
            status_code=500,
            detail="Clerk is not configured. Set CLERK_SECRET_KEY in your .env file.",
        )
    return clerk_client


def require_auth(request: Request) -> dict:
    """Verify the Clerk session JWT and return the decoded payload.

    The frontend must attach the session token as:
        Authorization: Bearer <clerk_session_token>
    """
    client = _get_clerk_client()
    request_state = client.authenticate_request(
        request,
        AuthenticateRequestOptions(
            authorized_parties=CLERK_AUTHORIZED_PARTIES,
        ),
    )
    if not request_state.is_signed_in:
        raise HTTPException(
            status_code=401,
            detail=f"Not authenticated: {request_state.reason}",
        )
    return request_state.payload


def require_admin(request: Request) -> dict:
    """Verify the Clerk session JWT and ensure the user has the admin role.

    The user's publicMetadata must contain { "role": "admin" }.
    This is embedded in the session token via Clerk Dashboard → Sessions → Customize token.
    """
    payload = require_auth(request)
    role = (payload.get("metadata") or {}).get("role")
    if role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required. Your role does not have permission for this action.",
        )
    return payload


# Type aliases for use with FastAPI Depends()
AuthUser = Annotated[dict, Depends(require_auth)]
AdminUser = Annotated[dict, Depends(require_admin)]
