"""Document listing and deletion endpoints (owner or admin)."""

from urllib.parse import unquote

from fastapi import APIRouter, Depends, HTTPException

from app.auth import require_auth
from app.companies import DEFAULT_COMPANY_ID, company_raw_docs_dir, is_company_owner
from app.documents import delete_document, list_documents
from app.routes.companies import invalidate_doc_count

router = APIRouter(tags=["documents"])


def _authorized(payload: dict, company_id: str) -> bool:
    """Owner or admin may manage a company's documents."""
    user_id = payload.get("sub", "")
    role = (payload.get("metadata") or {}).get("role")
    return role == "admin" or is_company_owner(company_id, user_id)


@router.get("/documents")
def documents(
    company: str = DEFAULT_COMPANY_ID,
    payload: dict = Depends(require_auth),
) -> list[dict]:
    """List documents for a company (owner or admin)."""
    company_id = company or DEFAULT_COMPANY_ID
    if not _authorized(payload, company_id):
        raise HTTPException(
            status_code=403,
            detail="You can only view documents of your own companies.",
        )
    return list_documents(company_id)


@router.delete("/documents/{filename}", status_code=200)
def delete_document_route(
    filename: str,
    company: str = DEFAULT_COMPANY_ID,
    payload: dict = Depends(require_auth),
) -> dict:
    """Delete a single uploaded document (owner or admin).

    Removes the file from disk, MongoDB GridFS, and its chunks from the
    company's Chroma collection.
    """
    company_id = company or DEFAULT_COMPANY_ID
    if not _authorized(payload, company_id):
        raise HTTPException(
            status_code=403,
            detail="You can only delete documents of your own companies.",
        )

    name = unquote(filename)

    # 1. Remove chunks from the company's vector store (source contains the file name)
    try:
        from app.ingestion.embedder import get_embedding_model
        from app.rag.vectorstore import load_vectorstore

        vecstore = load_vectorstore(get_embedding_model(), company_id)
        existing = vecstore.get(where={"source": {"$contains": name}})
        ids = existing.get("ids") or []
        if ids:
            vecstore.delete(ids=ids)
    except Exception:
        pass  # vector store may be unavailable; disk/GridFS are authoritative

    # 2. Remove the file from disk (raw_docs plus any reingest_cache copy)
    import shutil
    from pathlib import Path

    from app.config import COMPANIES_DIR

    dirs = [company_raw_docs_dir(company_id), COMPANIES_DIR / company_id / "reingest_cache"]
    for d in dirs:
        f = Path(d) / name
        if f.exists():
            if f.is_dir():
                shutil.rmtree(f, ignore_errors=True)
            else:
                f.unlink(missing_ok=True)

    # 3. Remove from persistent MongoDB GridFS
    deleted = delete_document(company_id, name)
    if deleted:
        invalidate_doc_count(company_id)

    return {"detail": f"Document '{name}' deleted.", "deleted": deleted}