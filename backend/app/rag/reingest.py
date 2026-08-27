"""Startup re-ingestion: rebuild Chroma collections from MongoDB GridFS.

Render's local disk is ephemeral, so ChromaDB embeddings written at runtime
are wiped on every restart. Documents stored in GridFS survive, so this module
rebuilds each company's vector collection from those documents on boot.
"""

import asyncio
import logging
import shutil
from pathlib import Path

from app.companies import get_company
from app.config import COMPANIES_DIR
from app.documents import iter_company_documents
from app.ingestion.chunker import chunk_documents
from app.ingestion.embedder import get_embedding_model
from app.ingestion.loader import load_documents
from app.rag.vectorstore import delete_company_collection, load_vectorstore

logger = logging.getLogger("supportiq.reingest")


def _cache_dir(company_id: str) -> Path:
    """Ephemeral folder used to stage GridFS files for ingestion."""
    return COMPANIES_DIR / company_id / "reingest_cache"


async def reingest_company(company_id: str) -> int:
    """Rebuild one company's collection from its GridFS documents."""
    files = list(iter_company_documents(company_id))
    if not files:
        return 0

    cache = _cache_dir(company_id)
    shutil.rmtree(cache, ignore_errors=True)
    cache.mkdir(parents=True, exist_ok=True)
    for filename, data in files:
        (cache / filename).write_bytes(data)

    try:
        delete_company_collection(company_id)
    except Exception as exc:  # collection may not exist yet
        logger.warning("Could not clear collection for %s: %s", company_id, exc)

    documents = load_documents(str(cache))
    chunks = chunk_documents(documents)
    if chunks:
        await load_vectorstore(get_embedding_model(), company_id).aadd_documents(chunks)
    logger.info("Re-ingested %d chunks for company %s", len(chunks), company_id)
    return len(chunks)


async def reingest_all() -> None:
    """Rebuild collections for every company that has documents in GridFS."""
    from app.companies import list_companies

    for info in list_companies():
        try:
            await reingest_company(info.id)
        except Exception as exc:
            logger.warning("Re-ingest failed for %s: %s", info.id, exc)


async def run_reingest() -> None:
    """Fire-and-forget re-ingestion started shortly after boot."""
    try:
        await asyncio.sleep(2)  # let the server finish booting first
        await reingest_all()
    except Exception as exc:
        logger.warning("Background re-ingestion failed: %s", exc)