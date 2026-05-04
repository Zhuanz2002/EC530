import pytest

from app.messaging.event_schema import EventValidationError, create_event, validate_event
from app.messaging.topics import IMAGE_SUBMITTED


def test_valid_event_passes():
    event = create_event(IMAGE_SUBMITTED, {"image_id": "img_001"})
    assert validate_event(event) == event


def test_missing_topic_fails():
    event = create_event(IMAGE_SUBMITTED, {"image_id": "img_001"})
    event.pop("topic")
    with pytest.raises(EventValidationError):
        validate_event(event)


def test_missing_event_id_fails():
    event = create_event(IMAGE_SUBMITTED, {"image_id": "img_001"})
    event.pop("event_id")
    with pytest.raises(EventValidationError):
        validate_event(event)


def test_unknown_topic_fails():
    event = create_event(IMAGE_SUBMITTED, {"image_id": "img_001"})
    event["topic"] = "unknown.topic"
    with pytest.raises(EventValidationError):
        validate_event(event)


def test_malformed_event_rejected_without_crashing():
    with pytest.raises(EventValidationError):
        validate_event("not a dict")
