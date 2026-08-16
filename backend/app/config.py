"""Application configuration loaded from environment / .env."""

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")

GROQ_API_KEY: str | None = os.getenv("GROQ_API_KEY")
LANGCHAIN_API_KEY: str | None = os.getenv("LANGCHAIN_API_KEY")
LANGCHAIN_TRACING_V2: bool = os.getenv("LANGCHAIN_TRACING_V2", "true").lower() == "true"
LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "supportiq")

RAW_DOCS_DIR = BACKEND_DIR / "data" / "raw_docs"  # legacy flat folder (kept for reference)
COMPANIES_DIR = BACKEND_DIR / "data" / "companies"
CHROMA_DIR = BACKEND_DIR / "data" / "chroma_db"
