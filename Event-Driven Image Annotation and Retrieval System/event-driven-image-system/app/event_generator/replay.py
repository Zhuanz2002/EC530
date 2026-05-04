"""Replay stored JSON events through a bus."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


def load_events(path: str) -> list[dict[str, Any]]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def replay_events(bus, path: str, delay_seconds: float = 0.0) -> int:
    count = 0
    for event in load_events(path):
        event_delay = float(event.get("payload", {}).get("_delay_seconds", delay_seconds))
        if event_delay:
            time.sleep(event_delay)
        topic = event.get("topic")
        if topic:
            bus.publish(topic, event)
            count += 1
    return count
