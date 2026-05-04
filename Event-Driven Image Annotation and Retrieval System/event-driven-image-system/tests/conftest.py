from __future__ import annotations

from typing import Any

import pytest


class RecordingBusDouble:
    def __init__(self) -> None:
        self.published: list[tuple[str, dict[str, Any]]] = []
        self.subscribers: dict[str, list] = {}

    def publish(self, topic: str, event: dict[str, Any]) -> int:
        self.published.append((topic, event))
        for callback in self.subscribers.get(topic, []):
            callback(event)
        return len(self.subscribers.get(topic, []))

    def subscribe(self, topic: str, callback) -> None:
        self.subscribers.setdefault(topic, []).append(callback)


@pytest.fixture
def RecordingBus():
    return RecordingBusDouble()
