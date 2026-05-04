from app.db.repositories import InMemoryAnnotationRepository
from app.services.document_db_service import DocumentDBService
from app.services.embedding_service import EmbeddingService
from app.services.inference_service import InferenceService
from app.vector.embedding_simulator import EmbeddingSimulator


def test_malformed_events_are_logged_and_services_do_not_crash(RecordingBus):
    bad = {"type": "publish", "payload": {}}
    InferenceService(RecordingBus).handle_event(bad)
    DocumentDBService(RecordingBus, InMemoryAnnotationRepository()).handle_event(bad)
    EmbeddingService(RecordingBus, EmbeddingSimulator()).handle_event(bad)
    assert len(RecordingBus.published) == 3
    assert all(topic == "error.logged" for topic, _ in RecordingBus.published)
