"""Document upload endpoint: save files, run ingestion, append to the vector store."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.auth import require_auth
from app.companies import DEFAULT_COMPANY_ID, company_raw_docs_dir, is_company_owner
from app.documents import save_document
from app.ingestion.chunker import chunk_documents
from app.ingestion.embedder import get_embedding_model
from app.ingestion.loader import load_documents
from app.rag.vectorstore import load_vectorstore
from app.routes.companies import invalidate_doc_count

router = APIRouter(tags=["upload"])


@router.post("/upload")
async def upload(
    files: list[UploadFile] = File(...),
    company: str = Form(DEFAULT_COMPANY_ID),
    payload: dict = Depends(require_auth),
) -> dict:
    """Authenticated users can upload docs for their own companies.
    Admins can upload for any company.
    """
    company_id = company or DEFAULT_COMPANY_ID
    user_id = payload.get("sub", "")
    role = (payload.get("metadata") or {}).get("role")

    # Non-admin users can only upload to their own companies
    if role != "admin" and not is_company_owner(company_id, user_id):
        raise HTTPException(
            status_code=403,
            detail="You can only upload documents to your own companies.",
        )

    company_dir = company_raw_docs_dir(company_id)
    company_dir.mkdir(parents=True, exist_ok=True)

    vectorstore = load_vectorstore(get_embedding_model(), company_id)

    results: list[dict] = []
    for file in files:
        raw = await file.read()
        # Persist to MongoDB GridFS so uploads survive restarts
        try:
            save_document(company_id, file.filename, raw)
        except Exception:
            pass  # fall back to disk-only storage if MongoDB is unavailable

        dest = company_dir / file.filename
        dest.write_bytes(raw)

        docs = load_documents(str(dest))
        chunks = chunk_documents(docs)
        if chunks:
            await vectorstore.aadd_documents(chunks)

        results.append(
            {
                "filename": file.filename,
                "chunks_added": len(chunks),
            }
        )

    invalidate_doc_count(company_id)

    return {
        "company": company_id,
        "files": len(results),
        "chunks_added": sum(r["chunks_added"] for r in results),
        "results": results,
    }
