"""Image submission service."""

from __future__ import annotations

from uuid import uuid4

from app.messaging.event_schema import create_event
from app.messaging.topics import IMAGE_SUBMITTED


class ImageService:
    """Accepts simulated uploads and publishes image.submitted events."""

    def __init__(self, bus) -> None:
        self.bus = bus

    def submit_image(self, path: str, source: str) -> dict:
        image_id = f"img_{uuid4().hex[:8]}"
        event = create_event(IMAGE_SUBMITTED, {"image_id": image_id, "path": path, "source": source})
        self.bus.publish(IMAGE_SUBMITTED, event)
        return event
