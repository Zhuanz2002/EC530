"""Deterministic event generator with failure injection."""

from __future__ import annotations

import random
from typing import Any

from app.messaging.event_schema import create_event
from app.messaging.topics import IMAGE_SUBMITTED


class EventGenerator:
    def __init__(self, seed: int | None = None) -> None:
        self.random = random.Random(seed)

    def image_events(
        self,
        count: int,
        duplicates: bool = False,
        malformed: bool = False,
        dropped: bool = False,
        delayed: bool = False,
    ) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        for i in range(count):
            if dropped and i % 5 == 0:
                continue
            event = create_event(
                IMAGE_SUBMITTED,
                {
                    "image_id": f"img_{i:03d}",
                    "path": f"images/generated_{i:03d}.jpg",
                    "source": f"camera_{self.random.choice(['A', 'B'])}",
                },
            )
            if delayed and i % 4 == 0:
                event["payload"]["_delay_seconds"] = 0.05
            events.append(event)
            if duplicates and i % 3 == 0:
                events.append(dict(event))
            if malformed and i % 4 == 0:
                bad = dict(event)
                bad.pop("topic", None)
                events.append(bad)
        return events
