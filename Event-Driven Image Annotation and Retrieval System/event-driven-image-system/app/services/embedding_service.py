"""Embedding creation service."""

from __future__ import annotations

from typing import Any

from app.messaging.event_schema import EventValidationError, create_event, validate_event
from app.messaging.topics import ANNOTATION_STORED, EMBEDDING_CREATED, ERROR_LOGGED
from app.vector.embedding_simulator import EmbeddingSimulator


class EmbeddingService:
    """Consumes annotation.stored and publishes deterministic object embeddings."""

    def __init__(self, bus, simulator: EmbeddingSimulator) -> None:
        self.bus = bus
        self.simulator = simulator

    def start(self) -> None:
        self.bus.subscribe(ANNOTATION_STORED, self.handle_event)

    def handle_event(self, event: dict[str, Any]) -> dict[str, Any] | None:
        try:
            validate_event(event)
            payload = event["payload"]
            embeddings = [
                {
                    "object_id": obj["object_id"],
                    "label": obj["label"],
                    "vector": self.simulator.embed_object(obj["label"], obj["object_id"]),
                }
                for obj in payload.get("objects", [])
            ]
            out = create_event(EMBEDDING_CREATED, {"image_id": payload["image_id"], "embeddings": embeddings})
        except (KeyError, EventValidationError, TypeError) as exc:
            self._log_error("malformed annotation.stored", str(exc), event)
            return None
        self.bus.publish(EMBEDDING_CREATED, out)
        return out

    def _log_error(self, message: str, detail: str, original: Any) -> None:
        self.bus.publish(ERROR_LOGGED, create_event(ERROR_LOGGED, {"message": message, "detail": detail, "original_event": original}))
