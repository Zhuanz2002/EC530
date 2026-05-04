"""Query service."""

from __future__ import annotations

from typing import Any

from app.messaging.event_schema import EventValidationError, create_event, validate_event
from app.messaging.topics import ERROR_LOGGED, QUERY_SUBMITTED


class QueryService:
    """Consumes query.submitted and asks the vector-index service layer for results."""

    def __init__(self, bus, vector_index_service) -> None:
        self.bus = bus
        self.vector_index_service = vector_index_service

    def start(self) -> None:
        self.bus.subscribe(QUERY_SUBMITTED, self.handle_event)

    def submit_query(self, text: str, top_k: int = 3) -> dict[str, Any]:
        event = create_event(QUERY_SUBMITTED, {"text": text, "top_k": top_k})
        self.bus.publish(QUERY_SUBMITTED, event)
        return event

    def handle_event(self, event: dict[str, Any]) -> dict[str, Any] | None:
        try:
            validate_event(event)
            payload = event["payload"]
            return self.vector_index_service.complete_query(event["event_id"], payload["text"], int(payload.get("top_k", 3)))
        except (KeyError, EventValidationError, TypeError, ValueError) as exc:
            self.bus.publish(ERROR_LOGGED, create_event(ERROR_LOGGED, {"message": "malformed query.submitted", "detail": str(exc), "original_event": event}))
            return None
