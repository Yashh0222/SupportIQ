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
from app.documents import count_documents_batch
from app.models.schemas import CreateCompanyRequest

router = APIRouter(tags=["companies"])

_DOC_COUNT_TTL_SECONDS = 60.0
_doc_count_cache: dict[str, tuple[float, int]] = {}


def _disk_doc_count(docs_dir: Path) -> int:
    """Legacy fallback: count files on the ephemeral disk (non-Mongo storage)."""
    if not docs_dir.exists():
        return 0
    return len([p for p in docs_dir.rglob("*") if p.is_file()])


def _doc_counts(company_ids: list[str]) -> dict[str, int]:
    """Return doc counts for many companies with one batched MongoDB query,
    cached in-process for a short TTL."""
    now = time.monotonic()
    result: dict[str, int] = {}
    missing: list[str] = []
    for cid in company_ids:
        cached = _doc_count_cache.get(cid)
        if cached is not None and now - cached[0] < _DOC_COUNT_TTL_SECONDS:
            result[cid] = cached[1]
        else:
            missing.append(cid)

    if missing:
        batch = count_documents_batch(missing)
        for cid in missing:
            count = batch.get(cid, 0)
            if count == 0:
                # fallback for legacy disk-only storage
                disk = _disk_doc_count(company_raw_docs_dir(cid))
                count = disk if disk else 0
            _doc_count_cache[cid] = (now, count)
            result[cid] = count
    return result


def invalidate_doc_count(company_id: str) -> None:
    """Drop the cached doc count so the next /companies call re-scans."""
    _doc_count_cache.pop(company_id, None)


@router.get("/companies")
def companies() -> list[dict]:
    companies_list = list_companies()
    counts = _doc_counts([c.id for c in companies_list])
    return [
        {
            "id": c.id,
            "display_name": c.display_name,
            "description": c.description,
            "doc_count": counts.get(c.id, 0),
        }
        for c in companies_list
    ]


@router.get("/companies/mine")
def my_companies(payload: dict = Depends(require_auth)) -> list[dict]:
    """Return companies owned by the current user."""
    user_id = payload.get("sub", "")
    owned = list_companies_for_owner(user_id)
    counts = _doc_counts([c.id for c in owned])
    return [
        {
            "id": c.id,
            "display_name": c.display_name,
            "description": c.description,
            "doc_count": counts.get(c.id, 0),
        }
        for c in owned
    ]


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
    is_admin = role == "admin"

    if not is_admin and not is_company_owner(company_id, user_id):
        raise HTTPException(status_code=403, detail="Only the company owner or admin can delete this company.")

    if not delete_company(company_id, allow_builtin=is_admin):
        # Non-admins can never delete built-in companies, so only return 404
        # when the company genuinely does not exist.
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
