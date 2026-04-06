import sqlite3

import pytest

from src.query_service import QueryService
from src.validator import SQLValidator


class GoodLLMAdapter:
    def generate_sql(self, user_request: str, schema_text: str) -> str:
        return "SELECT product_id, revenue FROM sales LIMIT 2"


class BadLLMAdapter:
    def generate_sql(self, user_request: str, schema_text: str) -> str:
        return "DROP TABLE sales;"


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")

    connection.execute(
        """
        CREATE TABLE sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            quantity INTEGER,
            revenue REAL,
            sale_date TEXT
        );
        """
    )

    connection.execute(
        """
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            product_name TEXT,
            category TEXT,
            price REAL
        );
        """
    )

    connection.executemany(
        "INSERT INTO sales (product_id, quantity, revenue, sale_date) VALUES (?, ?, ?, ?)",
        [
            (1, 2, 10.5, "2026-04-01"),
            (2, 1, 20.0, "2026-04-02"),
            (3, 5, 30.25, "2026-04-03"),
        ],
    )

    connection.executemany(
        "INSERT INTO products (product_id, product_name, category, price) VALUES (?, ?, ?, ?)",
        [
            (1, "Phone", "Electronics", 599.0),
            (2, "Laptop", "Electronics", 1299.0),
            (3, "Mouse", "Accessories", 25.0),
        ],
    )

    connection.commit()

    yield connection
    connection.close()


@pytest.fixture
def validator():
    return SQLValidator()


@pytest.fixture
def schema():
    return {
        "sales": {
            "product_id": "INTEGER",
            "quantity": "INTEGER",
            "revenue": "REAL",
            "sale_date": "TEXT",
        },
        "products": {
            "product_id": "INTEGER",
            "product_name": "TEXT",
            "category": "TEXT",
            "price": "REAL",
        },
    }


def test_list_tables_returns_created_tables(conn, validator):
    service = QueryService(conn=conn, validator=validator)

    tables = service.list_tables()

    assert "sales" in tables
    assert "products" in tables


def test_execute_validated_sql_returns_columns_rows_and_count(conn, validator, schema):
    service = QueryService(conn=conn, validator=validator)

    result = service.execute_validated_sql(
        "SELECT product_id, revenue FROM sales LIMIT 2",
        schema,
    )

    assert result["sql"] == "SELECT product_id, revenue FROM sales LIMIT 2"
    assert result["columns"] == ["product_id", "revenue"]
    assert len(result["rows"]) == 2
    assert result["row_count"] == 2


def test_execute_validated_sql_rejects_invalid_query_before_execution(conn, validator, schema):
    service = QueryService(conn=conn, validator=validator)

    with pytest.raises(ValueError, match="Only SELECT queries are allowed"):
        service.execute_validated_sql("DELETE FROM sales", schema)

    remaining = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    assert remaining == 3


def test_process_natural_language_query_uses_llm_then_validates_and_executes(conn, validator, schema):
    service = QueryService(
        conn=conn,
        validator=validator,
        llm_adapter=GoodLLMAdapter(),
    )

    result = service.process_natural_language_query(
        "show me two rows from sales",
        schema,
    )

    assert result["sql"] == "SELECT product_id, revenue FROM sales LIMIT 2"
    assert result["columns"] == ["product_id", "revenue"]
    assert len(result["rows"]) == 2
    assert result["row_count"] == 2


def test_process_natural_language_query_raises_when_llm_not_configured(conn, validator, schema):
    service = QueryService(conn=conn, validator=validator, llm_adapter=None)

    with pytest.raises(ValueError, match="LLM adapter is not configured"):
        service.process_natural_language_query("show me sales", schema)


def test_process_natural_language_query_rejects_empty_user_request(conn, validator, schema):
    service = QueryService(
        conn=conn,
        validator=validator,
        llm_adapter=GoodLLMAdapter(),
    )

    with pytest.raises(ValueError, match="User request cannot be empty"):
        service.process_natural_language_query("", schema)


def test_bad_llm_output_is_blocked_and_database_remains_correct(conn, validator, schema):
    service = QueryService(
        conn=conn,
        validator=validator,
        llm_adapter=BadLLMAdapter(),
    )

    with pytest.raises(ValueError, match="Only SELECT queries are allowed"):
        service.process_natural_language_query("delete the sales table", schema)

    tables = service.list_tables()
    assert "sales" in tables

    remaining = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    assert remaining == 3


def test_format_result_returns_human_readable_output(conn, validator, schema):
    service = QueryService(conn=conn, validator=validator)

    result = service.execute_validated_sql(
        "SELECT product_id, revenue FROM sales LIMIT 2",
        schema,
    )

    formatted = service.format_result(result)

    assert "product_id | revenue" in formatted
    assert "Rows returned: 2" in formatted


def test_format_result_handles_empty_results(conn, validator, schema):
    service = QueryService(conn=conn, validator=validator)

    result = service.execute_validated_sql(
        "SELECT product_id, revenue FROM sales WHERE product_id = 999",
        schema,
    )

    formatted = service.format_result(result)

    assert formatted == "No results found."


def test_build_schema_prompt_contains_table_and_column_information(conn, validator, schema):
    service = QueryService(conn=conn, validator=validator)

    prompt = service._build_schema_prompt(schema)

    assert "sales:" in prompt
    assert "product_id (INTEGER)" in prompt
    assert "products:" in prompt
    assert "product_name (TEXT)" in prompt
