"""Repository implementations for annotation documents and processed events."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Protocol


class AnnotationRepository(Protocol):
    def has_processed_event(self, event_id: str) -> bool: ...
    def mark_processed_event(self, event_id: str) -> None: ...
    def upsert_annotation(self, image_id: str, document: dict[str, Any]) -> None: ...
    def get_annotation(self, image_id: str) -> dict[str, Any] | None: ...


class MongoAnnotationRepository:
    """MongoDB-backed owner of image annotation documents."""

    def __init__(self, db) -> None:
        self.annotations = db["image_annotations"]
        self.processed_events = db["processed_events"]
        self.annotations.create_index("image_id", unique=True)
        self.processed_events.create_index("event_id", unique=True)

    def has_processed_event(self, event_id: str) -> bool:
        return self.processed_events.find_one({"event_id": event_id}) is not None

    def mark_processed_event(self, event_id: str) -> None:
        self.processed_events.update_one({"event_id": event_id}, {"$setOnInsert": {"event_id": event_id}}, upsert=True)

    def upsert_annotation(self, image_id: str, document: dict[str, Any]) -> None:
        self.annotations.update_one({"image_id": image_id}, {"$set": document}, upsert=True)

    def get_annotation(self, image_id: str) -> dict[str, Any] | None:
        doc = self.annotations.find_one({"image_id": image_id}, {"_id": 0})
        return dict(doc) if doc else None


class InMemoryAnnotationRepository:
    """Test double with MongoDB-like upsert semantics."""

    def __init__(self) -> None:
        self.annotations: dict[str, dict[str, Any]] = {}
        self.processed_events: set[str] = set()

    def has_processed_event(self, event_id: str) -> bool:
        return event_id in self.processed_events

    def mark_processed_event(self, event_id: str) -> None:
        self.processed_events.add(event_id)

    def upsert_annotation(self, image_id: str, document: dict[str, Any]) -> None:
        self.annotations[image_id] = deepcopy(document)

    def get_annotation(self, image_id: str) -> dict[str, Any] | None:
        doc = self.annotations.get(image_id)
        return deepcopy(doc) if doc else None
