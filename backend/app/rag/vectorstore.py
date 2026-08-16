"""ChromaDB vector store persistence for RAG — one collection per company."""

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.companies import DEFAULT_COMPANY_ID
from app.config import CHROMA_DIR
from app.ingestion.embedder import get_embedding_model

LEGACY_COLLECTION_NAME = "supportiq"


def _collection_name(company_id: str) -> str:
    return f"company_{company_id}"


def build_vectorstore(
    chunks: list[Document],
    embedding_model: Embeddings,
    company_id: str = DEFAULT_COMPANY_ID,
) -> Chroma:
    """Create and persist a Chroma collection for *company_id* from chunks."""
    return Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        collection_name=_collection_name(company_id),
        persist_directory=CHROMA_DIR,
    )


def load_vectorstore(
    embedding_model: Embeddings,
    company_id: str = DEFAULT_COMPANY_ID,
) -> Chroma:
    """Load (creating if needed) the persisted collection for *company_id*."""
    return Chroma(
        collection_name=_collection_name(company_id),
        embedding_function=embedding_model,
        persist_directory=CHROMA_DIR,
    )


def get_vectorstore(company_id: str = DEFAULT_COMPANY_ID) -> Chroma:
    """Load a company's vector store with the default embedding model."""
    return load_vectorstore(get_embedding_model(), company_id)
