"""Document upload endpoint: save files, run ingestion, append to the vector store."""

from fastapi import APIRouter, File, Form, UploadFile

from app.companies import DEFAULT_COMPANY_ID, company_raw_docs_dir
from app.ingestion.chunker import chunk_documents
from app.ingestion.embedder import get_embedding_model
from app.ingestion.loader import load_documents
from app.rag.vectorstore import load_vectorstore

router = APIRouter(tags=["upload"])


@router.post("/upload")
async def upload(
    files: list[UploadFile] = File(...),
    company: str = Form(DEFAULT_COMPANY_ID),
) -> dict:
    company_id = company or DEFAULT_COMPANY_ID
    company_dir = company_raw_docs_dir(company_id)
    company_dir.mkdir(parents=True, exist_ok=True)

    vectorstore = load_vectorstore(get_embedding_model(), company_id)

    results: list[dict] = []
    for file in files:
        dest = company_dir / file.filename
        dest.write_bytes(await file.read())

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

    return {
        "company": company_id,
        "files": len(results),
        "chunks_added": sum(r["chunks_added"] for r in results),
        "results": results,
    }
