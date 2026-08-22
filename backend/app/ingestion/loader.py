"""Document loading for the ingestion pipeline."""

import re
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document

TEXT_EXTENSIONS = {".md", ".txt", ".rst", ".html"}

_PDF_SPACE_RUN = re.compile(r"[ \t]{2,}")
_PDF_NEWLINE_RUN = re.compile(r"\n{3,}")


def _normalize_pdf_text(text: str) -> str:
    """Collapse spacing artifacts left behind by PDF text extraction."""
    text = _PDF_SPACE_RUN.sub(" ", text)
    text = re.sub(r" \n", "\n", text)
    return _PDF_NEWLINE_RUN.sub("\n\n", text).strip()


def load_documents(path: str) -> list[Document]:
    """Load all supported documents from *path* (a file or directory).
    Supported formats: markdown/text (.md, .txt, .rst, .html) via TextLoader
    and PDF via PyPDFLoader. PDF pages are whitespace-normalized because
    extractors often emit padded text that degrades embedding quality.
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
            pages = PyPDFLoader(str(file)).load()
            for page in pages:
                page.page_content = _normalize_pdf_text(page.page_content)
            docs.extend(pages)
        else:
            print(f"Skipping unsupported file: {file}")
    return docs
