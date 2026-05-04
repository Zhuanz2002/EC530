"""Redis Pub/Sub bus with safe JSON event handling."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

try:
    import redis
except ImportError:  # pragma: no cover - only used before installing requirements.
    redis = None

from app.config import settings
from app.messaging.event_schema import EventValidationError, validate_event

EventCallback = Callable[[dict[str, Any]], None]


class RedisBus:
    """Small adapter around redis-py's Pub/Sub primitives."""

    def __init__(self, client=None) -> None:
        if client is not None:
            self.client = client
        elif redis is None:
            raise RuntimeError("redis-py is not installed. Run: pip install -r requirements.txt")
        elif settings.redis_url:
            self.client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        else:
            self.client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                password=settings.redis_password,
                decode_responses=True,
            )

    def publish(self, topic: str, event: dict[str, Any]) -> int:
        validate_event(event)
        if event["topic"] != topic:
            raise EventValidationError("publish topic does not match event topic")
        return int(self.client.publish(topic, json.dumps(event)))

    def subscribe(self, topic: str, callback: EventCallback) -> None:
        pubsub = self.client.pubsub(ignore_subscribe_messages=True)
        pubsub.subscribe(topic)
        for message in pubsub.listen():
            raw = message.get("data")
            try:
                event = json.loads(raw)
                validate_event(event)
            except (TypeError, json.JSONDecodeError, EventValidationError):
                continue
            callback(event)
