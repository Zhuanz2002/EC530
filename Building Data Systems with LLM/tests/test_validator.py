import pytest

from src.validator import SQLValidator


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


def test_allows_simple_select(validator, schema):
    query = "SELECT * FROM sales"
    assert validator.validate(query, schema) is True


def test_allows_mixed_case_select(validator, schema):
    query = "SeLeCt product_id, revenue FROM sales"
    assert validator.validate(query, schema) is True


def test_rejects_empty_query(validator, schema):
    with pytest.raises(ValueError, match="Query cannot be empty"):
        validator.validate("", schema)


def test_rejects_non_select_insert(validator, schema):
    query = "INSERT INTO sales VALUES (1, 2, 3, '2026-04-06')"
    with pytest.raises(ValueError, match="Only SELECT queries are allowed"):
        validator.validate(query, schema)


def test_rejects_unknown_table(validator, schema):
    query = "SELECT * FROM unknown_table"
    with pytest.raises(ValueError, match="Unknown table referenced"):
        validator.validate(query, schema)


def test_rejects_unknown_column(validator, schema):
    query = "SELECT unknown_column FROM sales"
    with pytest.raises(ValueError, match="Unknown column referenced"):
        validator.validate(query, schema)


def test_rejects_multiple_statements_with_drop(validator, schema):
    query = "SELECT * FROM sales; DROP TABLE sales;"
    with pytest.raises(ValueError, match="dangerous SQL detected"):
        validator.validate(query, schema)


def test_allows_known_columns_with_where_and_limit(validator, schema):
    query = "SELECT product_id, revenue FROM sales WHERE quantity > 1 LIMIT 5"
    assert validator.validate(query, schema) is True


def test_allows_join_query_with_known_tables_and_columns(validator, schema):
    query = (
        "SELECT sales.product_id, products.product_name "
        "FROM sales JOIN products ON sales.product_id = products.product_id"
    )
    assert validator.validate(query, schema) is True


def test_allows_id_column_by_default(validator, schema):
    query = "SELECT id FROM sales"
    assert validator.validate(query, schema) is True
