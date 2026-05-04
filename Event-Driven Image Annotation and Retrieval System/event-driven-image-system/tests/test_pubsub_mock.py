from unittest.mock import Mock

from app.event_generator.generator import EventGenerator
from app.messaging.topics import IMAGE_SUBMITTED
from app.services.image_service import ImageService


def test_image_service_publish_called_with_correct_topic_and_event():
    bus = Mock()
    event = ImageService(bus).submit_image("images/street_001.jpg", "camera_A")
    bus.publish.assert_called_once()
    topic, published = bus.publish.call_args.args
    assert topic == IMAGE_SUBMITTED
    assert published == event
    assert published["payload"]["path"] == "images/street_001.jpg"


def test_generator_can_be_tested_by_mocking_publish():
    bus = Mock()
    events = EventGenerator(seed=42).image_events(2)
    for event in events:
        bus.publish(event["topic"], event)
    assert bus.publish.call_count == 2
    assert bus.publish.call_args_list[0].args[0] == IMAGE_SUBMITTED
