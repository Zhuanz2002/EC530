from __future__ import annotations

from pathlib import Path
import logging
import sqlite3
from typing import Dict

import pandas as pd


class SchemaManager:
    """
    Understand and manage SQLite table schemas.

    Responsibilities:
    - infer schema from CSV-loaded DataFrame
    - inspect existing SQLite tables
    - compare schema compatibility
    - create tables when needed

    This module does NOT handle natural-language queries or call the LLM.
    """

    SQLITE_TYPE_MAP = {
        "int64": "INTEGER",
        "int32": "INTEGER",
        "float64": "REAL",
        "float32": "REAL",
        "bool": "INTEGER",
    }

    def __init__(self, log_file: str = "error_log.txt") -> None:
        self.log_file = Path(log_file)
        logging.basicConfig(
            filename=self.log_file,
            level=logging.ERROR,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )

    def infer_schema(self, df: pd.DataFrame) -> Dict[str, str]:
        schema: Dict[str, str] = {}

        for column in df.columns:
            dtype_name = str(df[column].dtype)
            sqlite_type = self.SQLITE_TYPE_MAP.get(dtype_name, "TEXT")
            schema[column] = sqlite_type

        return schema

    def get_existing_tables(self, conn: sqlite3.Connection) -> list[str]:
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        )
        return [row[0] for row in cursor.fetchall()]

    def get_table_schema(self, conn: sqlite3.Connection, table_name: str) -> Dict[str, str]:
        self._validate_identifier(table_name)

        cursor = conn.execute(f"PRAGMA table_info({table_name});")
        rows = cursor.fetchall()

        if not rows:
            raise ValueError(f"Table does not exist or has no schema: {table_name}")

        schema: Dict[str, str] = {}

        for row in rows:
            column_name = row[1]
            column_type = (row[2] or "TEXT").upper()

            if column_name == "id":
                continue

            schema[column_name] = column_type

        return schema

    def schemas_match(self, inferred_schema: Dict[str, str], existing_schema: Dict[str, str]) -> bool:
        normalized_inferred = self._normalize_schema_dict(inferred_schema)
        normalized_existing = self._normalize_schema_dict(existing_schema)
        return normalized_inferred == normalized_existing

    def find_compatible_table(
        self, conn: sqlite3.Connection, inferred_schema: Dict[str, str]
    ) -> str | None:
        for table_name in self.get_existing_tables(conn):
            try:
                existing_schema = self.get_table_schema(conn, table_name)
                if self.schemas_match(inferred_schema, existing_schema):
                    return table_name
            except Exception as exc:
                self.log_error(f"Failed while checking schema for table '{table_name}': {exc}")

        return None

    def build_create_table_sql(self, table_name: str, schema: Dict[str, str]) -> str:
        self._validate_identifier(table_name)

        if not schema:
            raise ValueError("Schema cannot be empty.")

        column_defs = ["id INTEGER PRIMARY KEY AUTOINCREMENT"]

        for column_name, column_type in schema.items():
            self._validate_identifier(column_name)
            column_defs.append(f"{column_name} {column_type}")

        column_sql = ", ".join(column_defs)
        return f"CREATE TABLE {table_name} ({column_sql});"

    def create_table(self, conn: sqlite3.Connection, table_name: str, schema: Dict[str, str]) -> None:
        sql = self.build_create_table_sql(table_name, schema)
        conn.execute(sql)
        conn.commit()

    def log_error(self, message: str) -> None:
        logging.error(message)

    @staticmethod
    def _normalize_schema_dict(schema: Dict[str, str]) -> Dict[str, str]:
        return {
            str(column).strip().lower(): str(col_type).strip().upper()
            for column, col_type in schema.items()
        }

    @staticmethod
    def _validate_identifier(identifier: str) -> None:
        if not identifier or not identifier.replace("_", "").isalnum():
            raise ValueError(f"Invalid SQL identifier: {identifier}")
