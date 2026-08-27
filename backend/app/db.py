"""MongoDB connection layer (pymongo).

Creates one shared MongoClient on first use. If ``MONGODB_URI`` is not
configured, MongoDB is unavailable and the app falls back to log warnings
so the server can still boot locally without a database.
"""

from functools import lru_cache

import pymongo.errors
from pymongo import MongoClient

from app.config import MONGODB_DB_NAME, MONGODB_URI

_client: MongoClient | None = None


def get_client() -> MongoClient | None:
    """Return the shared MongoClient, or None if MongoDB is not configured."""
    global _client
    if _client is None and MONGODB_URI:
        _client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    return _client


def get_db():
    """Return the MongoDB database handle, or None if unavailable."""
    client = get_client()
    if client is None:
        return None
    try:
        # ping to surface connectivity errors early
        client.admin.command("ping")
    except pymongo.errors.PyMongoError:
        return None
    return client[MONGODB_DB_NAME]


def mongo_available() -> bool:
    try:
        return get_db() is not None
    except Exception:
        return False