"""Event construction and validation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.messaging.topics import ALLOWED_TOPICS

REQUIRED_FIELDS = {"type", "topic", "event_id", "timestamp", "payload"}


class EventValidationError(ValueError):
    """Raised when an event does not match the project event schema."""


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def new_event_id(prefix: str = "evt") -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def create_event(topic: str, payload: dict[str, Any], event_type: str = "publish") -> dict[str, Any]:
    event = {
        "type": event_type,
        "topic": topic,
        "event_id": new_event_id(),
        "timestamp": utc_now_iso(),
        "payload": payload,
    }
    validate_event(event)
    return event


def validate_event(event: Any) -> dict[str, Any]:
    if not isinstance(event, dict):
        raise EventValidationError("event must be a JSON object")
    missing = REQUIRED_FIELDS - set(event)
    if missing:
        raise EventValidationError(f"event missing required field(s): {', '.join(sorted(missing))}")
    if event["topic"] not in ALLOWED_TOPICS:
        raise EventValidationError(f"unknown topic: {event['topic']}")
    if not isinstance(event["payload"], dict):
        raise EventValidationError("payload must be a JSON object")
    if not event["event_id"]:
        raise EventValidationError("event_id must be non-empty")
    return event
