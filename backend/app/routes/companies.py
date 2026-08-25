"""Company registry endpoint: lists available company compartments and creates new ones."""

import time
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import require_auth
from app.companies import (
    CompanyInfo,
    company_raw_docs_dir,
    create_company,
    is_company_owner,
    list_companies,
    list_companies_for_owner,
)
from app.models.schemas import CreateCompanyRequest

router = APIRouter(tags=["companies"])

_DOC_COUNT_TTL_SECONDS = 60.0
_doc_count_cache: dict[str, tuple[float, int]] = {}


def _doc_count(company_id: str, docs_dir: Path) -> int:
    now = time.monotonic()
    cached = _doc_count_cache.get(company_id)
    if cached is not None and now - cached[0] < _DOC_COUNT_TTL_SECONDS:
        return cached[1]
    count = len([p for p in docs_dir.rglob("*") if p.is_file()]) if docs_dir.exists() else 0
    _doc_count_cache[company_id] = (now, count)
    return count


def invalidate_doc_count(company_id: str) -> None:
    """Drop the cached doc count so the next /companies call re-scans the folder."""
    _doc_count_cache.pop(company_id, None)


@router.get("/companies")
def companies() -> list[dict]:
    result = []
    for company in list_companies():
        result.append(
            {
                "id": company.id,
                "display_name": company.display_name,
                "description": company.description,
                "doc_count": _doc_count(company.id, company_raw_docs_dir(company.id)),
            }
        )
    return result


@router.get("/companies/mine")
def my_companies(payload: dict = Depends(require_auth)) -> list[dict]:
    """Return companies owned by the current user."""
    user_id = payload.get("sub", "")
    result = []
    for company in list_companies_for_owner(user_id):
        result.append(
            {
                "id": company.id,
                "display_name": company.display_name,
                "description": company.description,
                "doc_count": _doc_count(company.id, company_raw_docs_dir(company.id)),
            }
        )
    return result


@router.post("/companies", status_code=201)
def create_company_route(
    req: CreateCompanyRequest,
    payload: dict = Depends(require_auth),
) -> dict:
    """Any authenticated user can create a company."""
    user_id = payload.get("sub", "")
    try:
        info: CompanyInfo = create_company(
            req.id, req.display_name, req.description, owner_id=user_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return {
        "id": info.id,
        "display_name": info.display_name,
        "description": info.description,
        "doc_count": 0,
        "owner_id": info.owner_id,
    }
