"""Embedding model factory for the ingestion pipeline."""

import os
from functools import lru_cache

from langchain_jina import JinaEmbeddings

MODEL_NAME = "jina-embeddings-v3"
JINA_API_KEY = os.getenv("JINA_API_KEY")


@lru_cache(maxsize=1)
def get_embedding_model() -> JinaEmbeddings:
    """Return a cached Jina API-based embedding model instance."""
    return JinaEmbeddings(
        model=MODEL_NAME,
        jina_api_key=JINA_API_KEY,
        task="text-embedding",
    )
