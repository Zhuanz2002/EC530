from __future__ import annotations

import sqlite3
from typing import Any, Dict


class QueryService:
    """
    Coordinate the query flow:
    CLI -> QueryService -> LLM Adapter -> Validator -> SQLite

    Responsibilities:
    - receive SQL or natural-language query requests
    - validate generated SQL before execution
    - execute validated SELECT queries safely
    - format results for the CLI layer
    """

    def __init__(self, conn: sqlite3.Connection, validator: Any, llm_adapter: Any | None = None) -> None:
        self.conn = conn
        self.validator = validator
        self.llm_adapter = llm_adapter

    def list_tables(self) -> list[str]:
        cursor = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;"
        )
        return [row[0] for row in cursor.fetchall()]

    def execute_validated_sql(
        self, sql_query: str, schema: Dict[str, Dict[str, str]]
    ) -> Dict[str, Any]:
        self.validator.validate(sql_query, schema)

        cursor = self.conn.execute(sql_query)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description] if cursor.description else []

        return {
            "sql": sql_query,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
        }

    def process_natural_language_query(
        self, user_request: str, schema: Dict[str, Dict[str, str]]
    ) -> Dict[str, Any]:
        if self.llm_adapter is None:
            raise ValueError("LLM adapter is not configured.")

        if not user_request or not user_request.strip():
            raise ValueError("User request cannot be empty.")

        schema_text = self._build_schema_prompt(schema)
        sql_query = self.llm_adapter.generate_sql(user_request, schema_text)

        return self.execute_validated_sql(sql_query, schema)

    def format_result(self, result: Dict[str, Any]) -> str:
        columns = result.get("columns", [])
        rows = result.get("rows", [])

        if not rows:
            return "No results found."

        output_lines = []
        output_lines.append(" | ".join(columns))
        output_lines.append("-" * max(3, len(output_lines[0])))

        for row in rows:
            output_lines.append(" | ".join(str(value) for value in row))

        output_lines.append(f"\nRows returned: {result.get('row_count', 0)}")
        return "\n".join(output_lines)

    @staticmethod
    def _build_schema_prompt(schema: Dict[str, Dict[str, str]]) -> str:
        parts = []

        for table_name, columns in schema.items():
            column_text = ", ".join(f"{column} ({col_type})" for column, col_type in columns.items())
            parts.append(f"{table_name}: {column_text}")

        return "\n".join(parts)
