"""Company registry endpoint: lists available company compartments and creates new ones."""

import time
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import require_admin, require_auth
from app.companies import (
    CompanyInfo,
    company_raw_docs_dir,
    create_company,
    delete_company,
    is_company_owner,
    list_companies,
    list_companies_for_owner,
)
from app.documents import count_documents
from app.models.schemas import CreateCompanyRequest

router = APIRouter(tags=["companies"])

_DOC_COUNT_TTL_SECONDS = 60.0
_doc_count_cache: dict[str, tuple[float, int]] = {}


def _doc_count(company_id: str, docs_dir: Path) -> int:
    now = time.monotonic()
    cached = _doc_count_cache.get(company_id)
    if cached is not None and now - cached[0] < _DOC_COUNT_TTL_SECONDS:
        return cached[1]
    count = count_documents(company_id)
    if count == 0 and docs_dir.exists():
        # fallback for legacy disk-only storage
        count = len([p for p in docs_dir.rglob("*") if p.is_file()])
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


@router.delete("/companies/{company_id}")
def delete_company_route(
    company_id: str,
    payload: dict = Depends(require_auth),
) -> dict:
    """Delete a company. Owner or admin can delete."""
    user_id = payload.get("sub", "")
    role = (payload.get("metadata") or {}).get("role")

    if role != "admin" and not is_company_owner(company_id, user_id):
        raise HTTPException(status_code=403, detail="Only the company owner or admin can delete this company.")

    if not delete_company(company_id):
        raise HTTPException(status_code=404, detail="Company not found or is a built-in company.")

    # Clean up files, vector store, and persistent documents
    import shutil
    from app.config import COMPANIES_DIR as _COMPANIES_DIR
    from app.documents import delete_company_documents

    delete_company_documents(company_id)

    docs_dir = _COMPANIES_DIR / company_id
    if docs_dir.exists():
        shutil.rmtree(docs_dir, ignore_errors=True)

    try:
        from app.rag.vectorstore import delete_company_collection
        delete_company_collection(company_id)
    except Exception:
        pass

    invalidate_doc_count(company_id)
    return {"detail": f"Company '{company_id}' deleted."}
