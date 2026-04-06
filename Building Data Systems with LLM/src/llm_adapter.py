from __future__ import annotations

import os
import re
from abc import ABC, abstractmethod


class BaseLLMAdapter(ABC):
    """
    Abstract interface for translating natural language into SQL.
    This module does NOT execute SQL.
    """

    @abstractmethod
    def generate_sql(self, user_request: str, schema_text: str) -> str:
        raise NotImplementedError


class MockLLMAdapter(BaseLLMAdapter):
    """
    Simple local adapter for development and testing.
    Lets the project run without paying for an external API.
    """

    def generate_sql(self, user_request: str, schema_text: str) -> str:
        request = user_request.strip().lower()

        table_names = self._extract_table_names(schema_text)
        default_table = table_names[0] if table_names else None

        if not default_table:
            raise ValueError("No table information available for SQL generation.")

        if "list tables" in request or "show tables" in request:
            return "SELECT name FROM sqlite_master WHERE type='table';"

        if "count" in request or "how many" in request:
            return f"SELECT COUNT(*) AS total_count FROM {default_table};"

        if "top" in request and "5" in request:
            return f"SELECT * FROM {default_table} LIMIT 5;"

        if "all" in request or "show" in request or "list" in request:
            return f"SELECT * FROM {default_table} LIMIT 10;"

        return f"SELECT * FROM {default_table} LIMIT 5;"

    @staticmethod
    def _extract_table_names(schema_text: str) -> list[str]:
        names = []
        for line in schema_text.splitlines():
            line = line.strip()
            if not line or ":" not in line:
                continue
            table_name = line.split(":", 1)[0].strip()
            if table_name:
                names.append(table_name)
        return names


class OpenAILLMAdapter(BaseLLMAdapter):
    """
    Optional OpenAI-backed adapter.
    Requires:
    - OPENAI_API_KEY in environment variables
    - openai package installed
    """

    def __init__(self, model: str | None = None) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set.")

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ImportError(
                "openai package is not installed. Run: pip install openai"
            ) from exc

        self.client = OpenAI(api_key=api_key)
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def generate_sql(self, user_request: str, schema_text: str) -> str:
        if not user_request or not user_request.strip():
            raise ValueError("User request cannot be empty.")

        prompt = self._build_prompt(user_request, schema_text)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You convert natural language questions into SQLite SELECT queries. "
                        "Return SQL only. Do not include explanations, markdown, or code fences. "
                        "Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, or PRAGMA."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )

        sql = response.choices[0].message.content.strip()
        sql = self._extract_sql(sql)

        if not sql:
            raise ValueError("LLM returned an empty SQL response.")

        return sql

    @staticmethod
    def _build_prompt(user_request: str, schema_text: str) -> str:
        return (
            "Database schema:\n"
            f"{schema_text}\n\n"
            "User request:\n"
            f"{user_request}\n\n"
            "Generate one valid SQLite SELECT query only."
        )

    @staticmethod
    def _extract_sql(text: str) -> str:
        cleaned = text.strip()

        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
            cleaned = re.sub(r"\n?```$", "", cleaned).strip()

        return cleaned


def build_llm_adapter() -> BaseLLMAdapter:
    """
    Default factory:
    - if OPENAI_API_KEY exists -> use OpenAI adapter
    - otherwise -> use mock adapter
    """
    if os.getenv("OPENAI_API_KEY"):
        return OpenAILLMAdapter()

    return MockLLMAdapter()
