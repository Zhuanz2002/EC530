"""Simulated object detection service."""

from __future__ import annotations

import hashlib
from typing import Any

from app.messaging.event_schema import EventValidationError, create_event, validate_event
from app.messaging.topics import ERROR_LOGGED, IMAGE_SUBMITTED, INFERENCE_COMPLETED


LABELS = ["car", "person", "dog", "bicycle", "tree"]


class InferenceService:
    """Consumes image.submitted and publishes deterministic inference results."""

    def __init__(self, bus) -> None:
        self.bus = bus

    def start(self) -> None:
        self.bus.subscribe(IMAGE_SUBMITTED, self.handle_event)

    def handle_event(self, event: dict[str, Any]) -> dict[str, Any] | None:
        try:
            validate_event(event)
            payload = event["payload"]
            image_id = payload["image_id"]
            path = payload["path"]
        except (KeyError, EventValidationError, TypeError) as exc:
            self._log_error("malformed image.submitted", str(exc), event)
            return None
        objects = self._detect(image_id, path)
        out = create_event(
            INFERENCE_COMPLETED,
            {
                "image_id": image_id,
                "path": path,
                "source": payload.get("source"),
                "objects": objects,
                "model_version": "simulated-v1",
            },
        )
        self.bus.publish(INFERENCE_COMPLETED, out)
        return out

    def _detect(self, image_id: str, path: str) -> list[dict[str, Any]]:
        seed = int(hashlib.sha256(f"{image_id}:{path}".encode()).hexdigest(), 16)
        count = seed % 3 + 1
        objects = []
        for i in range(count):
            label = LABELS[(seed + i) % len(LABELS)]
            objects.append(
                {
                    "object_id": f"{image_id}_obj_{i + 1}",
                    "label": label,
                    "bbox": [20 + i * 30, 40, 150 + i * 20, 180 + i * 15],
                    "confidence": round(0.75 + ((seed >> (i * 4)) % 20) / 100, 2),
                }
            )
        return objects

    def _log_error(self, message: str, detail: str, original: Any) -> None:
        event = create_event(ERROR_LOGGED, {"message": message, "detail": detail, "original_event": original})
        self.bus.publish(ERROR_LOGGED, event)
