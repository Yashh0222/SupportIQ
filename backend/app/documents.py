"""Persistent document storage via MongoDB GridFS.

Uploaded PDFs/text files are stored in MongoDB GridFS so they survive backend
restarts (Render's local disk is ephemeral). Each file carries ``company_id``
metadata for per-company queries. If MongoDB is not configured, documents are
kept on disk only (fallback behavior).
"""

from typing import Iterator

import gridfs
from bson import ObjectId

from app.db import get_db

_FIELDS = {"_id": 0, "filename": 1, "length": 1}


def _gridfs() -> tuple[gridfs.GridFS, object] | tuple[None, None]:
    """Return (GridFS bucket, documents collection) or (None, None)."""
    db = get_db()
    if db is None:
        return None, None
    return gridfs.GridFS(db), db["documents"]


def save_document(
    company_id: str,
    filename: str,
    data: bytes,
) -> ObjectId:
    """Store a document's bytes in GridFS and record metadata."""
    fs, docs = _gridfs()
    if fs is None:
        raise RuntimeError("MongoDB not configured; cannot persist documents.")
    existing = docs.find_one({"company_id": company_id, "filename": filename})
    if existing is not None:
        fs.delete(existing["file_id"])
        docs.delete_one({"company_id": company_id, "filename": filename})
    file_id = fs.put(data, filename=filename, metadata={"company_id": company_id})
    docs.update_one(
        {"company_id": company_id, "filename": filename},
        {"$set": {"file_id": file_id, "length": len(data)}},
        upsert=True,
    )
    return file_id


def list_documents(company_id: str) -> list[dict]:
    """Return metadata for all documents belonging to a company."""
    _, docs = _gridfs()
    if docs is None:
        return []
    return [
        {"filename": d.get("filename"), "length": d.get("length", 0)}
        for d in docs.find({"company_id": company_id}, _FIELDS)
    ]


def count_documents(company_id: str) -> int:
    """Number of uploaded documents for a company."""
    _, docs = _gridfs()
    if docs is None:
        return 0
    return docs.count_documents({"company_id": company_id})


def count_documents_batch(company_ids: list[str]) -> dict[str, int]:
    """Return {company_id: doc_count} for all *company_ids* in one query."""
    if not company_ids:
        return {}
    _, docs = _gridfs()
    if docs is None:
        return {}
    pipeline = [
        {"$match": {"company_id": {"$in": company_ids}}},
        {"$group": {"_id": "$company_id", "n": {"$sum": 1}}},
    ]
    result: dict[str, int] = {cid: 0 for cid in company_ids}
    for row in docs.aggregate(pipeline):
        result[row["_id"]] = row["n"]
    return result


def read_document(company_id: str, filename: str) -> bytes | None:
    """Read a document's bytes back from GridFS by filename."""
    fs, docs = _gridfs()
    if fs is None:
        return None
    meta = docs.find_one({"company_id": company_id, "filename": filename})
    if meta is None:
        return None
    return fs.get(meta["file_id"]).read()


def iter_company_documents(company_id: str) -> Iterator[tuple[str, bytes]]:
    """Yield (filename, bytes) for every document of a company."""
    for meta in list_documents(company_id):
        data = read_document(company_id, meta["filename"])
        if data is not None:
            yield meta["filename"], data


def delete_company_documents(company_id: str) -> int:
    """Remove all documents (GridFS + metadata) for a company."""
    fs, docs = _gridfs()
    if fs is None:
        return 0
    file_ids = [d.get("file_id") for d in docs.find({"company_id": company_id})]
    for fid in file_ids:
        if fid is not None:
            fs.delete(fid)
    result = docs.delete_many({"company_id": company_id})
    return result.deleted_count if result else 0