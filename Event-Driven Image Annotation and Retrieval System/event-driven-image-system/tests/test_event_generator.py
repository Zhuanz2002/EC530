from app.event_generator.generator import EventGenerator


def test_generator_can_inject_duplicate_events():
    events = EventGenerator(seed=1).image_events(4, duplicates=True)
    event_ids = [event["event_id"] for event in events if "event_id" in event]
    assert len(event_ids) > len(set(event_ids))


def test_generator_can_inject_malformed_events():
    events = EventGenerator(seed=1).image_events(4, malformed=True)
    assert any("topic" not in event for event in events)


def test_generator_can_drop_events():
    events = EventGenerator(seed=1).image_events(10, dropped=True)
    assert len(events) < 10


def test_generator_can_inject_delayed_events():
    events = EventGenerator(seed=1).image_events(5, delayed=True)
    assert any(event["payload"].get("_delay_seconds") for event in events)


def test_subscriber_downtime_publish_has_no_subscribers(RecordingBus):
    delivered = RecordingBus.publish("image.submitted", {"topic": "image.submitted"})
    assert delivered == 0
    assert len(RecordingBus.published) == 1
