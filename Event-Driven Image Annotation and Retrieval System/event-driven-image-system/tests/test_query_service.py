from app.messaging.event_schema import create_event
from app.messaging.topics import QUERY_COMPLETED, QUERY_SUBMITTED
from app.services.query_service import QueryService
from app.services.vector_index_service import VectorIndexService
from app.vector.embedding_simulator import EmbeddingSimulator
from app.vector.faiss_index import FaissVectorIndex


def test_query_submitted_publishes_query_completed(RecordingBus):
    simulator = EmbeddingSimulator(8)
    index = FaissVectorIndex(8)
    index.add_embedding(simulator.embed_text("car"), {"image_id": "img_1", "object_id": "obj_1", "label": "car"})
    vector_service = VectorIndexService(RecordingBus, index, simulator)
    query_service = QueryService(RecordingBus, vector_service)
    event = create_event(QUERY_SUBMITTED, {"text": "car", "top_k": 1})
    out = query_service.handle_event(event)
    assert out["topic"] == QUERY_COMPLETED
    assert out["payload"]["results"][0]["label"] == "car"
