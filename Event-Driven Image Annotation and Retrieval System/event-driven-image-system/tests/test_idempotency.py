from app.db.repositories import InMemoryAnnotationRepository
from app.messaging.event_schema import create_event
from app.messaging.topics import EMBEDDING_CREATED, INFERENCE_COMPLETED
from app.services.document_db_service import DocumentDBService
from app.services.vector_index_service import VectorIndexService
from app.vector.embedding_simulator import EmbeddingSimulator
from app.vector.faiss_index import FaissVectorIndex


def inference_event():
    return create_event(
        INFERENCE_COMPLETED,
        {
            "image_id": "img_001",
            "path": "images/city_001.jpg",
            "source": "camera_A",
            "objects": [{"object_id": "img_001_obj_1", "label": "car", "bbox": [1, 2, 3, 4], "confidence": 0.9}],
            "model_version": "simulated-v1",
        },
    )


def test_duplicate_inference_event_does_not_create_duplicate_document_state(RecordingBus):
    repo = InMemoryAnnotationRepository()
    service = DocumentDBService(RecordingBus, repo)
    event = inference_event()
    service.handle_event(event)
    service.handle_event(event)
    assert len(repo.annotations) == 1
    assert len(repo.processed_events) == 1


def test_duplicate_embedding_event_does_not_add_duplicate_metadata(RecordingBus):
    simulator = EmbeddingSimulator(8)
    index = FaissVectorIndex(8)
    service = VectorIndexService(RecordingBus, index, simulator)
    event = create_event(
        EMBEDDING_CREATED,
        {"image_id": "img_001", "embeddings": [{"object_id": "img_001_obj_1", "label": "car", "vector": simulator.embed_text("car")}]},
    )
    service.handle_event(event)
    service.handle_event(event)
    assert len(index.metadata) == 1
