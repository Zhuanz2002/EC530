from app.messaging.event_schema import create_event
from app.messaging.topics import ANNOTATION_STORED, EMBEDDING_CREATED
from app.services.embedding_service import EmbeddingService
from app.vector.embedding_simulator import EmbeddingSimulator


def test_same_label_gives_deterministic_embedding():
    simulator = EmbeddingSimulator(dim=8)
    assert simulator.embed_object("car", "a") == simulator.embed_object("car", "b")


def test_embedding_dimension_is_correct():
    assert len(EmbeddingSimulator(dim=8).embed_text("person")) == 8


def test_annotation_stored_creates_embedding_created(RecordingBus):
    service = EmbeddingService(RecordingBus, EmbeddingSimulator(dim=8))
    event = create_event(
        ANNOTATION_STORED,
        {"image_id": "img_001", "objects": [{"object_id": "img_001_obj_1", "label": "car"}]},
    )
    out = service.handle_event(event)
    assert out["topic"] == EMBEDDING_CREATED
    assert out["payload"]["embeddings"][0]["label"] == "car"
    assert len(out["payload"]["embeddings"][0]["vector"]) == 8
