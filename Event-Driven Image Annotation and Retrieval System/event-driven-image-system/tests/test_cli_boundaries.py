from pathlib import Path


def test_cli_does_not_import_database_or_vector_adapters_directly():
    cli_source = Path("app/cli.py").read_text(encoding="utf-8")
    forbidden_imports = [
        "app.db.",
        "app.vector.faiss_index",
        "app.vector.embedding_simulator",
        "MongoAnnotationRepository",
        "FaissVectorIndex",
    ]
    for forbidden in forbidden_imports:
        assert forbidden not in cli_source


def test_runtime_wires_database_and_vector_adapters_outside_cli():
    runtime_source = Path("app/runtime.py").read_text(encoding="utf-8")
    assert "MongoAnnotationRepository" in runtime_source
    assert "FaissVectorIndex" in runtime_source
