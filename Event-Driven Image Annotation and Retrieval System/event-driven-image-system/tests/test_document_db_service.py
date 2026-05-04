from app.db.repositories import InMemoryAnnotationRepository
from app.messaging.event_schema import create_event
from app.messaging.topics import ANNOTATION_STORED, INFERENCE_COMPLETED
from app.services.document_db_service import DocumentDBService


def test_inference_completed_stores_mongodb_style_document(RecordingBus):
    repo = InMemoryAnnotationRepository()
    service = DocumentDBService(RecordingBus, repo)
    event = create_event(
        INFERENCE_COMPLETED,
        {
            "image_id": "img_001",
            "path": "images/city_001.jpg",
            "source": "camera_A",
            "objects": [{"object_id": "img_001_obj_1", "label": "car", "bbox": [20, 40, 150, 180], "confidence": 0.91}],
            "model_version": "simulated-v1",
        },
    )
    out = service.handle_event(event)
    doc = repo.get_annotation("img_001")
    assert doc["image_id"] == "img_001"
    assert isinstance(doc["objects"], list)
    assert doc["objects"][0]["label"] == "car"
    assert doc["review"]["status"] == "auto"
    assert out["topic"] == ANNOTATION_STORED
    assert RecordingBus.published[-1][0] == ANNOTATION_STORED
