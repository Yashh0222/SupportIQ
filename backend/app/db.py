"""MongoDB connection layer (pymongo).

Creates one shared MongoClient on first use. If ``MONGODB_URI`` is not
configured, MongoDB is unavailable and the app falls back to log warnings
so the server can still boot locally without a database.
"""

import time
from functools import lru_cache

import pymongo.errors
from pymongo import MongoClient

from app.config import MONGODB_DB_NAME, MONGODB_URI

_client: MongoClient | None = None
_available: bool | None = None
_available_checked_at: float = 0.0
_AVAILABILITY_TTL_SECONDS = 10.0


def get_client() -> MongoClient | None:
    """Return the shared MongoClient, or None if MongoDB is not configured."""
    global _client
    if _client is None and MONGODB_URI:
        _client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    return _client


def _refresh_availability() -> bool:
    """Ping Mongo once and cache the result for a short TTL to avoid
    a network round-trip on every call (e.g. per-company in /companies)."""
    global _available, _available_checked_at
    now = time.monotonic()
    if _available is not None and now - _available_checked_at < _AVAILABILITY_TTL_SECONDS:
        return _available
    client = get_client()
    ok = False
    if client is not None:
        try:
            client.admin.command("ping")
            ok = True
        except pymongo.errors.PyMongoError:
            ok = False
    _available = ok
    _available_checked_at = now
    return ok


def get_db():
    """Return the MongoDB database handle, or None if unavailable."""
    if not _refresh_availability():
        return None
    return get_client()[MONGODB_DB_NAME]


def mongo_available() -> bool:
    return _refresh_availability()