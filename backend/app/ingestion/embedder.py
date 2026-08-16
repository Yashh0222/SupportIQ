"""Embedding model factory for the ingestion pipeline."""

from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings

MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model() -> HuggingFaceEmbeddings:
    """Return a cached HuggingFace embedding model instance."""
    return HuggingFaceEmbeddings(model_name=MODEL_NAME)
