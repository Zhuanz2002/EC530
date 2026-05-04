import json

from app.messaging.event_schema import create_event
from app.messaging.redis_bus import RedisBus
from app.messaging.topics import IMAGE_SUBMITTED


class FakeRedisClient:
    def __init__(self):
        self.calls = []

    def publish(self, topic, message):
        self.calls.append((topic, message))
        return 1


def test_redis_bus_serializes_valid_event_as_json():
    client = FakeRedisClient()
    bus = RedisBus(client=client)
    event = create_event(IMAGE_SUBMITTED, {"image_id": "img_001"})
    delivered = bus.publish(IMAGE_SUBMITTED, event)
    topic, raw = client.calls[0]
    assert delivered == 1
    assert topic == IMAGE_SUBMITTED
    assert json.loads(raw) == event
