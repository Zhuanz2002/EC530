import pytest

from src.llm_adapter import MockLLMAdapter, build_llm_adapter


def test_mock_adapter_raises_when_schema_has_no_table():
    adapter = MockLLMAdapter()

    with pytest.raises(ValueError, match="No table information available"):
        adapter.generate_sql("show all rows", "")


def test_mock_adapter_generates_count_query():
    adapter = MockLLMAdapter()
    schema_text = "sales: product_id (INTEGER), revenue (REAL)"

    sql = adapter.generate_sql("how many rows are there", schema_text)

    assert sql == "SELECT COUNT(*) AS total_count FROM sales;"


def test_mock_adapter_generates_limit_query_for_top_5():
    adapter = MockLLMAdapter()
    schema_text = "sales: product_id (INTEGER), revenue (REAL)"

    sql = adapter.generate_sql("show top 5 rows", schema_text)

    assert sql == "SELECT * FROM sales LIMIT 5;"


def test_mock_adapter_generates_show_all_query():
    adapter = MockLLMAdapter()
    schema_text = "sales: product_id (INTEGER), revenue (REAL)"

    sql = adapter.generate_sql("show all data", schema_text)

    assert sql == "SELECT * FROM sales LIMIT 10;"


def test_mock_adapter_uses_first_table_as_default():
    adapter = MockLLMAdapter()
    schema_text = (
        "sales: product_id (INTEGER), revenue (REAL)\n"
        "products: product_id (INTEGER), product_name (TEXT)"
    )

    sql = adapter.generate_sql("list everything", schema_text)

    assert sql == "SELECT * FROM sales LIMIT 10;"


def test_mock_adapter_returns_sql_string():
    adapter = MockLLMAdapter()
    schema_text = "sales: product_id (INTEGER), revenue (REAL)"

    sql = adapter.generate_sql("show sales", schema_text)

    assert isinstance(sql, str)
    assert sql.strip().lower().startswith("select")


def test_build_llm_adapter_returns_mock_when_no_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    adapter = build_llm_adapter()

    assert isinstance(adapter, MockLLMAdapter)


def test_mock_adapter_does_not_execute_sql():
    adapter = MockLLMAdapter()
    schema_text = "sales: product_id (INTEGER), revenue (REAL)"

    sql = adapter.generate_sql("delete everything", schema_text)

    assert isinstance(sql, str)
    assert "drop table" not in sql.lower()
    assert "delete from" not in sql.lower()
