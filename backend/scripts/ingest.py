"""One-off ingestion script: docs -> chunks -> embeddings -> ChromaDB.

Run from the backend/ directory:
    python scripts/ingest.py --company acmecrm
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.companies import DEFAULT_COMPANY_ID, company_raw_docs_dir
from app.ingestion.chunker import chunk_documents
from app.ingestion.embedder import get_embedding_model
from app.ingestion.loader import load_documents
from app.rag.vectorstore import build_vectorstore


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest a company's documents.")
    parser.add_argument("--company", default=DEFAULT_COMPANY_ID, help="Company id")
    args = parser.parse_args()

    docs_dir = company_raw_docs_dir(args.company)
    docs = load_documents(str(docs_dir))
    if not docs:
        print(f"No supported documents found in {docs_dir}")
        return

    chunks = chunk_documents(docs)
    embedding_model = get_embedding_model()
    build_vectorstore(chunks, embedding_model, args.company)

    sources = sorted({doc.metadata.get("source", "unknown") for doc in docs})
    print(f"[{args.company}] Ingested {len(chunks)} chunks from {len(docs)} docs.")
    print("Sources:")
    for source in sources:
        print(f"  - {source}")


if __name__ == "__main__":
    main()
