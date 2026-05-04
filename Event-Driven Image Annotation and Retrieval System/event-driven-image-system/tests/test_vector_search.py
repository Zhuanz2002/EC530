from app.services.vector_index_service import VectorIndexService
from app.vector.embedding_simulator import EmbeddingSimulator
from app.vector.faiss_index import FaissVectorIndex


def test_faiss_index_can_add_vectors_and_search_top_k():
    simulator = EmbeddingSimulator(8)
    index = FaissVectorIndex(8)
    index.add_embedding(simulator.embed_text("car"), {"image_id": "img_1", "object_id": "obj_1", "label": "car"})
    index.add_embedding(simulator.embed_text("dog"), {"image_id": "img_2", "object_id": "obj_2", "label": "dog"})
    results = index.search(simulator.embed_text("car"), top_k=2)
    assert len(results) == 2
    assert results[0]["label"] == "car"


def test_query_for_car_returns_car_like_object_first(RecordingBus):
    simulator = EmbeddingSimulator(8)
    index = FaissVectorIndex(8)
    service = VectorIndexService(RecordingBus, index, simulator)
    index.add_embedding(simulator.embed_text("person"), {"image_id": "img_1", "object_id": "obj_1", "label": "person"})
    index.add_embedding(simulator.embed_text("car"), {"image_id": "img_2", "object_id": "obj_2", "label": "car"})
    results = service.search_by_text("car", top_k=1)
    assert len(results) == 1
    assert results[0]["label"] == "car"
