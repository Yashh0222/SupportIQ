"""Scratch script: load a company's vector store and run a similarity search.

Run from the backend/ directory:
    python scripts/search.py "what is your refund policy?" --company globex
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.companies import DEFAULT_COMPANY_ID
from app.rag.vectorstore import get_vectorstore


def main() -> None:
    parser = argparse.ArgumentParser(description="Search a company's vector store.")
    parser.add_argument("query", nargs="+", help="Search query words")
    parser.add_argument("--company", default=DEFAULT_COMPANY_ID, help="Company id")
    args = parser.parse_args()

    query = " ".join(args.query)
    vectorstore = get_vectorstore(args.company)
    results = vectorstore.similarity_search(query, k=3)

    print(f"Query: {query}  (company: {args.company})\n")
    if not results:
        print("No results found.")
        return
    for i, doc in enumerate(results, start=1):
        print(f"--- Result {i} ---")
        print(f"Source: {doc.metadata.get('source', 'unknown')}")
        print(doc.page_content)
        print()


if __name__ == "__main__":
    main()
