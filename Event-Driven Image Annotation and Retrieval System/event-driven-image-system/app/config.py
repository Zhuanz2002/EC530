"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency is installed from requirements in normal use.
    def load_dotenv() -> None:
        return None


load_dotenv()


@dataclass(frozen=True)
class Settings:
    redis_url: str | None = os.getenv("REDIS_URL")
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_password: str | None = os.getenv("REDIS_PASSWORD")
    mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    mongodb_db: str = os.getenv("MONGODB_DB", "image_annotation_project")
    faiss_index_path: str = os.getenv("FAISS_INDEX_PATH", "data/faiss.index")
    faiss_metadata_path: str = os.getenv("FAISS_METADATA_PATH", "data/faiss_metadata.json")
    embedding_dim: int = int(os.getenv("EMBEDDING_DIM", "8"))


settings = Settings()
