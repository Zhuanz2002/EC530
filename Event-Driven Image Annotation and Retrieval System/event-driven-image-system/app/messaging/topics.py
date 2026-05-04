"""Allowed event topics."""

IMAGE_SUBMITTED = "image.submitted"
INFERENCE_COMPLETED = "inference.completed"
ANNOTATION_STORED = "annotation.stored"
EMBEDDING_CREATED = "embedding.created"
QUERY_SUBMITTED = "query.submitted"
QUERY_COMPLETED = "query.completed"
ANNOTATION_CORRECTED = "annotation.corrected"
ERROR_LOGGED = "error.logged"

ALLOWED_TOPICS = {
    IMAGE_SUBMITTED,
    INFERENCE_COMPLETED,
    ANNOTATION_STORED,
    EMBEDDING_CREATED,
    QUERY_SUBMITTED,
    QUERY_COMPLETED,
    ANNOTATION_CORRECTED,
    ERROR_LOGGED,
}
