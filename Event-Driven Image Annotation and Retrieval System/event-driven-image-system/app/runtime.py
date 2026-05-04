"""Runtime wiring for services and infrastructure adapters."""

from __future__ import annotations

from app.config import settings
from app.db.mongo_client import get_mongo_database
from app.db.repositories import InMemoryAnnotationRepository, MongoAnnotationRepository
from app.messaging.redis_bus import RedisBus
from app.services.document_db_service import DocumentDBService
from app.services.embedding_service import EmbeddingService
from app.services.image_service import ImageService
from app.services.inference_service import InferenceService
from app.services.query_service import QueryService
from app.services.vector_index_service import VectorIndexService
from app.vector.embedding_simulator import EmbeddingSimulator
from app.vector.faiss_index import FaissVectorIndex


def build_runtime(bus=None, use_mongo: bool = True):
    """Build service objects while keeping infrastructure wiring out of the CLI."""

    bus = bus or RedisBus()
    simulator = EmbeddingSimulator(settings.embedding_dim)
    repository = MongoAnnotationRepository(get_mongo_database()) if use_mongo else InMemoryAnnotationRepository()
    index = FaissVectorIndex(settings.embedding_dim, settings.faiss_index_path, settings.faiss_metadata_path)
    vector_service = VectorIndexService(bus, index, simulator)
    services = {
        "image": ImageService(bus),
        "inference": InferenceService(bus),
        "document-db": DocumentDBService(bus, repository),
        "embedding": EmbeddingService(bus, simulator),
        "vector-index": vector_service,
        "query": QueryService(bus, vector_service),
    }
    return bus, services
