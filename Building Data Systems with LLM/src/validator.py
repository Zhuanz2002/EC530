from __future__ import annotations

import re
from typing import Dict


class SQLValidator:
    """
    Validate SQL queries before execution.

    Validation strategy:
    - only allow SELECT queries
    - reject unknown tables
    - reject unknown columns
    - operate at query-structure level, not full SQL parsing
    """

    SQL_KEYWORDS = {
        "select", "from", "where", "and", "or", "order", "by", "group", "limit",
        "having", "as", "asc", "desc", "count", "sum", "avg", "min", "max",
        "distinct", "like", "in", "between", "is", "null", "not", "on", "join",
        "inner", "left", "right", "outer"
    }

    def validate(self, query: str, schema: Dict[str, Dict[str, str]]) -> bool:
        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        cleaned_query = query.strip()
        lowered = cleaned_query.lower()

        self._validate_query_type(lowered)
        referenced_tables = self._extract_tables(lowered)

        if not referenced_tables:
            raise ValueError("No table referenced in query.")

        self._validate_tables(referenced_tables, schema)
        self._validate_columns(lowered, referenced_tables, schema)

        return True

    def _validate_query_type(self, lowered_query: str) -> None:
        if not lowered_query.startswith("select"):
            raise ValueError("Only SELECT queries are allowed.")

        blocked_patterns = [
            r";\s*drop\b",
            r";\s*delete\b",
            r";\s*insert\b",
            r";\s*update\b",
            r";\s*alter\b",
            r";\s*create\b",
            r";\s*replace\b",
            r";\s*pragma\b",
        ]

        for pattern in blocked_patterns:
            if re.search(pattern, lowered_query):
                raise ValueError("Multiple statements or dangerous SQL detected.")

    def _extract_tables(self, lowered_query: str) -> set[str]:
        tables = set()

        from_matches = re.findall(r"\bfrom\s+([a-zA-Z_][a-zA-Z0-9_]*)", lowered_query)
        join_matches = re.findall(r"\bjoin\s+([a-zA-Z_][a-zA-Z0-9_]*)", lowered_query)

        tables.update(from_matches)
        tables.update(join_matches)

        return tables

    def _validate_tables(self, referenced_tables: set[str], schema: Dict[str, Dict[str, str]]) -> None:
        known_tables = set(schema.keys())

        for table in referenced_tables:
            if table not in known_tables:
                raise ValueError(f"Unknown table referenced: {table}")

    def _validate_columns(
        self,
        lowered_query: str,
        referenced_tables: set[str],
        schema: Dict[str, Dict[str, str]],
    ) -> None:
        known_columns = {"id"}

        for table in referenced_tables:
            known_columns.update(col.lower() for col in schema[table].keys())

        candidate_tokens = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", lowered_query)

        ignored_tokens = set(referenced_tables) | self.SQL_KEYWORDS

        for token in candidate_tokens:
            if token in ignored_tokens:
                continue

            if token.isdigit():
                continue

            if token not in known_columns:
                raise ValueError(f"Unknown column referenced: {token}")
