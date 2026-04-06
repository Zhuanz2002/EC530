import sqlite3

import pandas as pd
import pytest

from src.schema_manager import SchemaManager


@pytest.fixture
def manager():
    return SchemaManager(log_file="test_error_log.txt")


@pytest.fixture
def sample_df():
    return pd.DataFrame(
        {
            "product_id": [1, 2, 3],
            "price": [10.5, 20.0, 30.25],
            "product_name": ["a", "b", "c"],
        }
    )


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    yield connection
    connection.close()


def test_infer_schema_maps_types_correctly(manager, sample_df):
    schema = manager.infer_schema(sample_df)

    assert schema == {
        "product_id": "INTEGER",
        "price": "REAL",
        "product_name": "TEXT",
    }


def test_build_create_table_sql_adds_primary_key(manager):
    schema = {
        "product_id": "INTEGER",
        "price": "REAL",
        "product_name": "TEXT",
    }

    sql = manager.build_create_table_sql("products", schema)

    assert sql.startswith("CREATE TABLE products")
    assert "id INTEGER PRIMARY KEY AUTOINCREMENT" in sql
    assert "product_id INTEGER" in sql
    assert "price REAL" in sql
    assert "product_name TEXT" in sql


def test_create_table_and_get_existing_tables(manager, conn):
    schema = {
        "product_id": "INTEGER",
        "price": "REAL",
    }

    manager.create_table(conn, "products", schema)
    tables = manager.get_existing_tables(conn)

    assert "products" in tables


def test_get_table_schema_reads_schema_without_id(manager, conn):
    schema = {
        "product_id": "INTEGER",
        "price": "REAL",
        "product_name": "TEXT",
    }

    manager.create_table(conn, "products", schema)
    retrieved = manager.get_table_schema(conn, "products")

    assert retrieved == schema


def test_schemas_match_returns_true_for_equivalent_schema(manager):
    inferred_schema = {
        "product_id": "INTEGER",
        "price": "REAL",
        "product_name": "TEXT",
    }

    existing_schema = {
        "product_id": "INTEGER",
        "price": "REAL",
        "product_name": "TEXT",
    }

    assert manager.schemas_match(inferred_schema, existing_schema) is True


def test_schemas_match_returns_false_for_different_column_names(manager):
    inferred_schema = {
        "product_id": "INTEGER",
        "price": "REAL",
    }

    existing_schema = {
        "item_id": "INTEGER",
        "price": "REAL",
    }

    assert manager.schemas_match(inferred_schema, existing_schema) is False


def test_schemas_match_returns_false_for_different_types(manager):
    inferred_schema = {
        "product_id": "INTEGER",
        "price": "REAL",
    }

    existing_schema = {
        "product_id": "TEXT",
        "price": "REAL",
    }

    assert manager.schemas_match(inferred_schema, existing_schema) is False


def test_find_compatible_table_returns_matching_table_name(manager, conn):
    schema = {
        "product_id": "INTEGER",
        "price": "REAL",
        "product_name": "TEXT",
    }

    manager.create_table(conn, "products", schema)

    found = manager.find_compatible_table(conn, schema)

    assert found == "products"


def test_find_compatible_table_returns_none_when_no_match(manager, conn):
    existing_schema = {
        "product_id": "INTEGER",
        "price": "REAL",
    }
    inferred_schema = {
        "product_id": "INTEGER",
        "price": "REAL",
        "product_name": "TEXT",
    }

    manager.create_table(conn, "products", existing_schema)

    found = manager.find_compatible_table(conn, inferred_schema)

    assert found is None


def test_build_create_table_sql_rejects_invalid_table_name(manager):
    schema = {"product_id": "INTEGER"}

    with pytest.raises(ValueError, match="Invalid SQL identifier"):
        manager.build_create_table_sql("bad-table-name", schema)


def test_get_table_schema_raises_for_missing_table(manager, conn):
    with pytest.raises(ValueError, match="Table does not exist"):
        manager.get_table_schema(conn, "missing_table")
