"""Document loading for the ingestion pipeline."""

from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document

TEXT_EXTENSIONS = {".md", ".txt", ".rst", ".html"}


def load_documents(path: str) -> list[Document]:
    """Load all supported documents from *path* (a file or directory).

    Supported formats: markdown/text (.md, .txt, .rst, .html) via TextLoader
    and PDF via PyPDFLoader.
    """
    path = Path(path)
    if path.is_file():
        files = [path]
    elif path.is_dir():
        files = sorted(p for p in path.rglob("*") if p.is_file())
    else:
        raise FileNotFoundError(f"Path does not exist: {path}")

    docs: list[Document] = []
    for file in files:
        suffix = file.suffix.lower()
        if suffix in TEXT_EXTENSIONS:
            docs.extend(TextLoader(str(file), encoding="utf-8").load())
        elif suffix == ".pdf":
            docs.extend(PyPDFLoader(str(file)).load())
        else:
            print(f"Skipping unsupported file: {file}")
    return docs
