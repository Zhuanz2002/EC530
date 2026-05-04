"""FAISS vector index wrapper with metadata persistence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

try:
    import faiss  # type: ignore
except ImportError:  # pragma: no cover - used only when faiss-cpu is unavailable locally.
    faiss = None


class _NumpyFlatL2:
    """Tiny compatibility fallback so unit tests can run without compiled FAISS installed."""

    def __init__(self, dim: int) -> None:
        self.dim = dim
        self.vectors = np.empty((0, dim), dtype="float32")

    @property
    def ntotal(self) -> int:
        return len(self.vectors)

    def add(self, vectors: np.ndarray) -> None:
        self.vectors = np.vstack([self.vectors, vectors.astype("float32")])

    def search(self, queries: np.ndarray, top_k: int):
        distances = ((self.vectors[None, :, :] - queries[:, None, :]) ** 2).sum(axis=2)
        idx = np.argsort(distances, axis=1)[:, :top_k]
        dist = np.take_along_axis(distances, idx, axis=1)
        return dist.astype("float32"), idx.astype("int64")


class FaissVectorIndex:
    """Owns vector storage, FAISS search, and metadata mapping."""

    def __init__(self, dim: int, index_path: str | None = None, metadata_path: str | None = None) -> None:
        self.dim = dim
        self.index_path = Path(index_path) if index_path else None
        self.metadata_path = Path(metadata_path) if metadata_path else None
        self.metadata: list[dict[str, Any]] = []
        self._object_keys: set[str] = set()
        self.index = self._new_index()
        self.load()

    def _new_index(self):
        if faiss is None:
            return _NumpyFlatL2(self.dim)
        return faiss.IndexFlatL2(self.dim)

    def add_embedding(self, vector: list[float], metadata: dict[str, Any]) -> bool:
        key = f"{metadata.get('image_id')}::{metadata.get('object_id')}"
        if key in self._object_keys:
            return False
        arr = np.asarray([vector], dtype="float32")
        if arr.shape != (1, self.dim):
            raise ValueError(f"expected vector dimension {self.dim}")
        self.index.add(arr)
        self.metadata.append(dict(metadata))
        self._object_keys.add(key)
        return True

    def search(self, vector: list[float], top_k: int = 3) -> list[dict[str, Any]]:
        if self.index.ntotal == 0:
            return []
        arr = np.asarray([vector], dtype="float32")
        limit = min(top_k, self.index.ntotal)
        distances, indices = self.index.search(arr, limit)
        results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx < 0:
                continue
            item = dict(self.metadata[int(idx)])
            item["score"] = float(distance)
            results.append(item)
        return results

    def save(self) -> None:
        if self.index_path and faiss is not None:
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            faiss.write_index(self.index, str(self.index_path))
        elif self.index_path and isinstance(self.index, _NumpyFlatL2):
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            np.save(str(self.index_path) + ".npy", self.index.vectors)
        if self.metadata_path:
            self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
            self.metadata_path.write_text(json.dumps(self.metadata, indent=2), encoding="utf-8")

    def load(self) -> None:
        vectors_loaded = False
        if self.index_path and self.index_path.exists() and faiss is not None:
            self.index = faiss.read_index(str(self.index_path))
            vectors_loaded = True
        elif self.index_path and faiss is None:
            fallback_path = Path(str(self.index_path) + ".npy")
            if fallback_path.exists():
                self.index.vectors = np.load(fallback_path).astype("float32")
                vectors_loaded = True
        elif self.index_path is None:
            vectors_loaded = True
        if self.metadata_path and self.metadata_path.exists() and vectors_loaded:
            self.metadata = json.loads(self.metadata_path.read_text(encoding="utf-8"))
            self._object_keys = {f"{m.get('image_id')}::{m.get('object_id')}" for m in self.metadata}
