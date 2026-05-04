"""Vector index owner service."""

from __future__ import annotations

from typing import Any

from app.messaging.event_schema import EventValidationError, create_event, validate_event
from app.messaging.topics import EMBEDDING_CREATED, ERROR_LOGGED, QUERY_COMPLETED
from app.vector.embedding_simulator import EmbeddingSimulator


class VectorIndexService:
    """Consumes embedding.created and owns the FAISS vector index."""

    def __init__(self, bus, index, simulator: EmbeddingSimulator) -> None:
        self.bus = bus
        self.index = index
        self.simulator = simulator
        self.processed_objects: set[str] = set()

    def start(self) -> None:
        self.bus.subscribe(EMBEDDING_CREATED, self.handle_event)

    def handle_event(self, event: dict[str, Any]) -> None:
        try:
            validate_event(event)
            payload = event["payload"]
            image_id = payload["image_id"]
            for item in payload.get("embeddings", []):
                key = f"{image_id}::{item['object_id']}"
                if key in self.processed_objects:
                    continue
                added = self.index.add_embedding(
                    item["vector"],
                    {"image_id": image_id, "object_id": item["object_id"], "label": item["label"]},
                )
                if added:
                    self.processed_objects.add(key)
            self.index.save()
        except (KeyError, EventValidationError, TypeError, ValueError) as exc:
            self._log_error("malformed embedding.created", str(exc), event)

    def search_by_vector(self, vector: list[float], top_k: int = 3) -> list[dict[str, Any]]:
        return self.index.search(vector, top_k)

    def search_by_text(self, text: str, top_k: int = 3) -> list[dict[str, Any]]:
        return self.search_by_vector(self.simulator.embed_text(text), top_k)

    def complete_query(self, query_id: str, text: str, top_k: int) -> dict[str, Any]:
        results = self.search_by_text(text, top_k)
        event = create_event(QUERY_COMPLETED, {"query_id": query_id, "text": text, "results": results})
        self.bus.publish(QUERY_COMPLETED, event)
        return event

    def _log_error(self, message: str, detail: str, original: Any) -> None:
        self.bus.publish(ERROR_LOGGED, create_event(ERROR_LOGGED, {"message": message, "detail": detail, "original_event": original}))
