"""Origin approval requests: users request origins, admin approves.

When a user creates a company and wants to embed the widget on their site,
they submit an origin request. The admin reviews and approves it, which
adds the origin to the allowed list.

Data is persisted to ``data/companies/origin_requests.json``.
"""

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from app.config import COMPANIES_DIR

REQUESTS_FILE = COMPANIES_DIR / "origin_requests.json"


@dataclass
class OriginRequest:
    id: str
    user_id: str
    user_email: str
    company_id: str
    origin: str
    reason: str
    status: str  # "pending" | "approved" | "rejected"
    created_at: float
    resolved_at: float = 0.0


def _load_requests() -> list[dict]:
    if not REQUESTS_FILE.exists():
        return []
    try:
        return json.loads(REQUESTS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _save_requests(requests: list[dict]) -> None:
    REQUESTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    REQUESTS_FILE.write_text(json.dumps(requests, indent=2), encoding="utf-8")


def create_request(
    request_id: str,
    user_id: str,
    user_email: str,
    company_id: str,
    origin: str,
    reason: str = "",
) -> OriginRequest:
    """Create a new pending origin request."""
    req = OriginRequest(
        id=request_id,
        user_id=user_id,
        user_email=user_email,
        company_id=company_id,
        origin=origin,
        reason=reason,
        status="pending",
        created_at=time.time(),
    )
    requests = _load_requests()
    requests.append(asdict(req))
    _save_requests(requests)
    return req


def list_requests(status: str | None = None) -> list[OriginRequest]:
    """List all requests, optionally filtered by status."""
    requests = _load_requests()
    result = [OriginRequest(**r) for r in requests]
    if status:
        result = [r for r in result if r.status == status]
    return result


def list_requests_for_user(user_id: str) -> list[OriginRequest]:
    """List all requests made by a specific user."""
    requests = _load_requests()
    return [OriginRequest(**r) for r in requests if r["user_id"] == user_id]


def resolve_request(request_id: str, status: str) -> OriginRequest | None:
    """Approve or reject a request. Returns the updated request or None."""
    requests = _load_requests()
    for r in requests:
        if r["id"] == request_id:
            r["status"] = status
            r["resolved_at"] = time.time()
            _save_requests(requests)
            return OriginRequest(**r)
    return None
