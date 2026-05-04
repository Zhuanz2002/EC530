# Event-Driven Image Annotation and Retrieval System

Python MVP for an EC530 event-driven software engineering project. The system simulates image upload, object inference, annotation storage, embedding creation, FAISS indexing, and top-k search without training any model or implementing ANN algorithms manually.

## Requirement Mapping

| Requirement | Implementation |
| --- | --- |
| P1 Tested Pub-Sub with Redis | `app/messaging/redis_bus.py` uses `redis` / redis-py Pub/Sub. Tests cover mocked publishing and RedisBus JSON serialization without requiring a live broker. |
| P2 Document DB with MongoDB | `MongoAnnotationRepository` stores image annotation documents in MongoDB. `DocumentDBService` is the sole owner of that collection. |
| P3 Simulated Image Processing / Embedding | `InferenceService` and `EmbeddingSimulator` produce deterministic fake detections and embeddings. No model is trained. |
| P4 Embedding DB / Vector Index with FAISS | `FaissVectorIndex` wraps `faiss.IndexFlatL2` and stores metadata for retrieval. |

## Architecture

```text
CLI / Event Generator
        |
        v
Redis Pub/Sub topics
        |
        +--> InferenceService ------ publishes inference.completed
        |
        +--> DocumentDBService ----- owns MongoDB annotations, publishes annotation.stored
        |
        +--> EmbeddingService ------ publishes embedding.created
        |
        +--> VectorIndexService ---- owns FAISS index and metadata
        |
        +--> QueryService ---------- publishes query.completed
```

The CLI/API does not directly import or mutate MongoDB or FAISS adapters. Infrastructure wiring is isolated in `app/runtime.py`; the CLI calls service entrypoints or publishes events. Services validate event envelopes before processing.

## Services And Data Ownership

| Service | Owns | Publishes | Consumes |
| --- | --- | --- | --- |
| ImageService | Simulated upload entrypoint | `image.submitted` | none |
| InferenceService | Simulated object detection logic | `inference.completed`, `error.logged` | `image.submitted` |
| DocumentDBService | MongoDB image annotation documents and processed event IDs | `annotation.stored`, `error.logged` | `inference.completed` |
| EmbeddingService | Embedding simulation for annotation objects | `embedding.created`, `error.logged` | `annotation.stored` |
| VectorIndexService | FAISS index and FAISS metadata mapping | `query.completed`, `error.logged` | `embedding.created` |
| QueryService | Query orchestration | `query.submitted`, `query.completed`, `error.logged` | `query.submitted` |

`app/runtime.py` is the composition root that wires Redis, MongoDB, FAISS, and services together. This keeps the CLI from bypassing service ownership boundaries.

## Topics

| Topic | Publisher | Subscriber | Purpose |
| --- | --- | --- | --- |
| `image.submitted` | ImageService, generator | InferenceService | New image entered the workflow |
| `inference.completed` | InferenceService | DocumentDBService | Simulated objects are ready to store |
| `annotation.stored` | DocumentDBService | EmbeddingService | MongoDB annotation document was upserted |
| `embedding.created` | EmbeddingService | VectorIndexService | Object vectors are ready for FAISS |
| `query.submitted` | QueryService / CLI | QueryService | Text query request |
| `query.completed` | QueryService / VectorIndexService | Clients/loggers | Search result event |
| `annotation.corrected` | Future review UI | Future services | Human correction event |
| `error.logged` | Any service | Logs/monitoring | Malformed event or processing failure |

## Event Schema

```json
{
  "type": "publish",
  "topic": "image.submitted",
  "event_id": "evt_1042",
  "timestamp": "2026-04-07T14:33:00Z",
  "payload": {
    "image_id": "img_1042",
    "path": "images/street_1042.jpg",
    "source": "camera_A"
  }
}
```

Validation requires `type`, `topic`, `event_id`, `timestamp`, and object-shaped `payload`. Topics must be in the allowed topic list in `app/messaging/topics.py`.

## Upload Event Flow

1. `ImageService.submit_image(path, source)` creates `image_id` and publishes `image.submitted`.
2. `InferenceService` consumes the event and publishes deterministic `inference.completed` objects.
3. `DocumentDBService` upserts one MongoDB document per `image_id`, records processed `event_id`, and publishes `annotation.stored`.
4. `EmbeddingService` creates one deterministic vector per object and publishes `embedding.created`.
5. `VectorIndexService` adds vectors to FAISS and persists metadata.

## Query Event Flow

1. A query is submitted as text, for example `car`, by publishing `query.submitted`.
2. `QueryService` consumes the event and routes through the vector-index service layer.
3. `VectorIndexService` converts text to a simulated embedding, searches FAISS top-k, and publishes `query.completed`.

## Design Justification

MongoDB is appropriate because image annotations are nested and variable: different images can have different object lists, bounding boxes, confidence values, review state, and history without forcing rigid relational joins.

Redis Pub/Sub is appropriate for the asynchronous workflow because image processing, persistence, embedding, and indexing are naturally decoupled. Each service can evolve independently and communicate through events.

FAISS is appropriate for top-k vector retrieval because it provides battle-tested vector search primitives. This project intentionally uses `IndexFlatL2` instead of manually implementing nearest-neighbor algorithms.

## Run Locally

Start Redis and MongoDB:

```bash
docker compose up -d
```

Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Copy environment defaults if desired:

```bash
cp .env.example .env
```

Run the synchronous service-boundary demo:

```bash
python -m app.cli demo
```

Run workers:

```bash
python -m app.cli run-worker --service inference
python -m app.cli run-worker --service document-db
python -m app.cli run-worker --service embedding
python -m app.cli run-worker --service vector-index
```

Submit and replay:

```bash
python -m app.cli upload --path images/street_001.jpg --source camera_A
python -m app.cli generate-events --count 10 --seed 42
python -m app.cli replay --file sample_data/events.json
python -m app.cli search --text "car" --top-k 3
```

`search` publishes a `query.submitted` event. Run the `query`/vector services through the demo or workers to produce `query.completed`.

Run tests:

```bash
pytest
```

## Failure Handling And Idempotency

Malformed events are validated and rejected without crashing services; services publish `error.logged` events where possible. Duplicate `inference.completed` events are ignored through processed event IDs. Duplicate embeddings do not create duplicate FAISS metadata because `VectorIndexService` tracks `image_id::object_id`.

The event generator supports deterministic events and injection of duplicate, malformed, delayed, and dropped messages:

```bash
python -m app.cli generate-events --count 10 --seed 42 --duplicates --malformed --delayed --dropped
python -m app.cli replay --file sample_data/events.json --delay 0.1
```

Subscriber downtime can be demonstrated by publishing while a Redis subscriber is not running; because Redis Pub/Sub is ephemeral, missed messages are expected. A production version would use Redis Streams, Kafka, or durable queues for replayable delivery.

## Test Strategy

Unit tests cover schema validation, mock pub-sub behavior, RedisBus JSON serialization, CLI/database boundary enforcement, idempotency, malformed events, MongoDB-style document creation through an in-memory repository, embedding determinism, query completion, event generator failure injection, and FAISS search. Tests are designed to pass without live Redis or MongoDB.

Current professor checklist status:

| Check | Status |
| --- | --- |
| Redis Pub/Sub tested system | Satisfied by `RedisBus`, mocked publish tests, and serialization tests. |
| MongoDB document database | Satisfied by `MongoAnnotationRepository` and `DocumentDBService` ownership. |
| Simulated image processing and embedding | Satisfied by deterministic inference and embedding simulator. |
| FAISS vector database | Satisfied by `FaissVectorIndex` using `faiss.IndexFlatL2` when `faiss-cpu` is installed. |
| CLI does not directly access databases | Satisfied by moving infrastructure wiring to `app/runtime.py` and testing CLI boundaries. |
| Unit tests for required failure cases | Satisfied by tests for schema, mocking, idempotency, malformed events, delayed/dropped/duplicate generation, subscriber downtime, and vector search. |

## Limitations And Future Work

This is an architecture-focused MVP. It does not store real image files, perform real ML inference, train models, implement ANN algorithms, or provide durable event replay. Future work could add a REST API, Redis Streams for durability, a review UI for `annotation.corrected`, integration tests against Docker services, and richer index lifecycle management.
