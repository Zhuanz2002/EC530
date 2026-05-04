"""Deterministic embedding simulation for labels and query text."""

from __future__ import annotations

import hashlib

import numpy as np


class EmbeddingSimulator:
    """Creates deterministic normalized vectors without training a model."""

    def __init__(self, dim: int = 8) -> None:
        self.dim = dim

    def embed_text(self, text: str) -> list[float]:
        canonical = text.strip().lower()
        digest = hashlib.sha256(canonical.encode("utf-8")).digest()
        values = np.frombuffer(digest, dtype=np.uint8)[: self.dim].astype("float32")
        vector = values / 255.0
        norm = float(np.linalg.norm(vector))
        if norm:
            vector = vector / norm
        return vector.astype("float32").tolist()

    def embed_object(self, label: str, object_id: str | None = None) -> list[float]:
        # Label dominates so same-label objects are identical and searchable by text.
        return self.embed_text(label)
