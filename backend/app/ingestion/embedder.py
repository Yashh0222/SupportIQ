"""Embedding model factory for the ingestion pipeline."""

import os
from functools import lru_cache
from typing import Any

import requests
from langchain_core.embeddings import Embeddings

MODEL_NAME = "jina-embeddings-v3"
JINA_API_KEY = os.getenv("JINA_API_KEY")
JINA_URL = "https://api.jina.ai/v1/embeddings"


class EmbeddingError(RuntimeError):
    """Raised when the upstream embedding API is unavailable or rejects a request."""


class JinaEmbeddings(Embeddings):
    """API-based Jina embedder using the native REST endpoint.

    Returns 768-dim vectors matching the model's output space.
    """

    def __init__(
        self,
        model: str = MODEL_NAME,
        api_key: str | None = JINA_API_KEY,
        task: str = "text-matching",
    ) -> None:
        if not api_key:
            raise EmbeddingError("JINA_API_KEY is not set")
        self.model = model
        self.api_key = api_key
        self.task = task

    def _embed(self, texts: list[str]) -> list[list[float]]:
        try:
            response = requests.post(
                JINA_URL,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "task": self.task,
                    "input": texts,
                    "embedding_type": "float",
                },
                timeout=60,
            )
        except requests.RequestException as exc:
            raise EmbeddingError(f"Could not reach Jina embeddings API: {exc}") from exc
        if not response.ok:
            body = (response.text or "")[:300]
            raise EmbeddingError(
                f"Jina embeddings API error {response.status_code}: {body}"
            )
        data = response.json()
        return [item["embedding"] for item in data.get("data", [])]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text])[0]


@lru_cache(maxsize=1)
def get_embedding_model() -> JinaEmbeddings:
    """Return a cached Jina API-based embedding model instance."""
    return JinaEmbeddings(task="text-matching")
