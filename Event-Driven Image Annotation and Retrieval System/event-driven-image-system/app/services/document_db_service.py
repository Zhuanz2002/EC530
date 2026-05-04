"""Document DB owner service."""

from __future__ import annotations

from typing import Any

from app.messaging.event_schema import EventValidationError, create_event, utc_now_iso, validate_event
from app.messaging.topics import ANNOTATION_STORED, ERROR_LOGGED, INFERENCE_COMPLETED


class DocumentDBService:
    """Consumes inference.completed and owns MongoDB annotation documents."""

    def __init__(self, bus, repository) -> None:
        self.bus = bus
        self.repository = repository

    def start(self) -> None:
        self.bus.subscribe(INFERENCE_COMPLETED, self.handle_event)

    def handle_event(self, event: dict[str, Any]) -> dict[str, Any] | None:
        try:
            validate_event(event)
            if self.repository.has_processed_event(event["event_id"]):
                return None
            payload = event["payload"]
            image_id = payload["image_id"]
            now = utc_now_iso()
            existing = self.repository.get_annotation(image_id) or {}
            document = {
                "image_id": image_id,
                "path": payload["path"],
                "source": payload.get("source"),
                "objects": payload.get("objects", []),
                "review": existing.get("review", {"status": "auto", "notes": []}),
                "history": ["submitted", "inference_completed", "annotation_stored"],
                "model_version": payload.get("model_version", "simulated-v1"),
                "created_at": existing.get("created_at", now),
                "updated_at": now,
            }
        except (KeyError, EventValidationError, TypeError) as exc:
            self._log_error("malformed inference.completed", str(exc), event)
            return None

        self.repository.upsert_annotation(image_id, document)
        self.repository.mark_processed_event(event["event_id"])
        out = create_event(
            ANNOTATION_STORED,
            {"image_id": image_id, "path": document["path"], "source": document["source"], "objects": document["objects"]},
        )
        self.bus.publish(ANNOTATION_STORED, out)
        return out

    def _log_error(self, message: str, detail: str, original: Any) -> None:
        self.bus.publish(ERROR_LOGGED, create_event(ERROR_LOGGED, {"message": message, "detail": detail, "original_event": original}))
