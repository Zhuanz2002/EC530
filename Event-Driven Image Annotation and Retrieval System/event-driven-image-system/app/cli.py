"""Command line interface for the event-driven image system."""

from __future__ import annotations

import argparse
import json
import threading
from pathlib import Path
from typing import Any

from app.event_generator.generator import EventGenerator
from app.event_generator.replay import replay_events
from app.messaging.event_schema import create_event, validate_event
from app.messaging.redis_bus import RedisBus
from app.messaging.topics import QUERY_COMPLETED, QUERY_SUBMITTED
from app.runtime import build_runtime


class SyncBus:
    """In-process bus for demo mode that preserves service boundaries."""

    def __init__(self) -> None:
        self.subscribers: dict[str, list] = {}
        self.events: list[tuple[str, dict[str, Any]]] = []

    def publish(self, topic: str, event: dict[str, Any]) -> int:
        self.events.append((topic, event))
        for callback in self.subscribers.get(topic, []):
            callback(event)
        return len(self.subscribers.get(topic, []))

    def subscribe(self, topic: str, callback) -> None:
        self.subscribers.setdefault(topic, []).append(callback)


def run_worker(service_name: str) -> None:
    _, services = build_runtime()
    service = services[service_name]
    print(f"Starting {service_name} worker")
    service.start()


def run_all_workers() -> None:
    _, services = build_runtime()
    names = ["inference", "document-db", "embedding", "vector-index"]
    for name in names:
        thread = threading.Thread(target=services[name].start, daemon=True)
        thread.start()
        print(f"Started {name} worker")
    print("Workers are listening. Press Ctrl+C to stop.")
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        print("Stopping workers")


def demo() -> None:
    bus = SyncBus()
    _, services = build_runtime(bus=bus, use_mongo=False)
    services["inference"].start()
    services["document-db"].start()
    services["embedding"].start()
    services["vector-index"].start()
    services["query"].start()
    images = [
        ("images/city_001.jpg", "camera_A"),
        ("images/street_002.jpg", "camera_B"),
        ("images/park_003.jpg", "camera_A"),
        ("images/garage_car_004.jpg", "camera_C"),
    ]
    for path, source in images:
        services["image"].submit_image(path, source)
    query_done: list[dict[str, Any]] = []
    bus.subscribe(QUERY_COMPLETED, query_done.append)
    services["query"].submit_query("car", top_k=3)
    print(json.dumps(query_done[-1]["payload"], indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Event-driven image annotation and retrieval system")
    sub = parser.add_subparsers(dest="command", required=True)

    upload = sub.add_parser("upload")
    upload.add_argument("--path", required=True)
    upload.add_argument("--source", required=True)

    gen = sub.add_parser("generate-events")
    gen.add_argument("--count", type=int, default=10)
    gen.add_argument("--seed", type=int, default=42)
    gen.add_argument("--output", default="sample_data/events.json")
    gen.add_argument("--duplicates", action="store_true")
    gen.add_argument("--malformed", action="store_true")
    gen.add_argument("--dropped", action="store_true")
    gen.add_argument("--delayed", action="store_true")

    replay = sub.add_parser("replay")
    replay.add_argument("--file", required=True)
    replay.add_argument("--delay", type=float, default=0.0)

    search = sub.add_parser("search")
    search.add_argument("--text", required=True)
    search.add_argument("--top-k", type=int, default=3)

    worker = sub.add_parser("run-worker")
    worker.add_argument("--service", required=True, choices=["inference", "document-db", "embedding", "vector-index"])

    sub.add_parser("run-all-workers")
    sub.add_parser("demo")

    args = parser.parse_args()
    if args.command == "upload":
        bus, services = build_runtime(use_mongo=False)
        event = services["image"].submit_image(args.path, args.source)
        print(json.dumps(event, indent=2))
    elif args.command == "generate-events":
        events = EventGenerator(args.seed).image_events(
            args.count,
            duplicates=args.duplicates,
            malformed=args.malformed,
            dropped=args.dropped,
            delayed=args.delayed,
        )
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(events, indent=2), encoding="utf-8")
        print(f"Wrote {len(events)} events to {args.output}")
    elif args.command == "replay":
        count = replay_events(RedisBus(), args.file, args.delay)
        print(f"Replayed {count} events")
    elif args.command == "search":
        event = create_event(QUERY_SUBMITTED, {"text": args.text, "top_k": args.top_k})
        validate_event(event)
        RedisBus().publish(QUERY_SUBMITTED, event)
        print(json.dumps(event, indent=2))
    elif args.command == "run-worker":
        run_worker(args.service)
    elif args.command == "run-all-workers":
        run_all_workers()
    elif args.command == "demo":
        demo()


if __name__ == "__main__":
    main()
