"""MongoDB client factory."""

from __future__ import annotations

try:
    from pymongo import MongoClient
except ImportError:  # pragma: no cover - only used before installing requirements.
    MongoClient = None

from app.config import settings


def get_mongo_database():
    if MongoClient is None:
        raise RuntimeError("pymongo is not installed. Run: pip install -r requirements.txt")
    client = MongoClient(settings.mongodb_uri)
    return client[settings.mongodb_db]
