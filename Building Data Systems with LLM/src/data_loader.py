from __future__ import annotations

from pathlib import Path
import re

import pandas as pd


class DataLoader:
    """
    Load CSV files into pandas DataFrames for downstream schema and database logic.
    This module only reads and validates CSV data. It does NOT write to SQLite.
    """

    SUPPORTED_EXTENSIONS = {".csv"}

    def load_csv(self, file_path: str | Path) -> pd.DataFrame:
        path = Path(file_path)
        self._validate_path(path)

        df = pd.read_csv(path)

        if df.empty:
            raise ValueError(f"CSV file is empty: {path}")

        df = df.copy()
        df.columns = [self.normalize_column_name(col) for col in df.columns]

        if len(set(df.columns)) != len(df.columns):
            raise ValueError("Duplicate column names detected after normalization.")

        return df

    def preview_rows(self, file_path: str | Path, n: int = 5) -> pd.DataFrame:
        path = Path(file_path)
        self._validate_path(path)
        return pd.read_csv(path, nrows=n)

    @staticmethod
    def normalize_column_name(name: str) -> str:
        normalized = name.strip().lower()
        normalized = re.sub(r"\s+", "_", normalized)
        normalized = re.sub(r"[^a-z0-9_]", "_", normalized)
        normalized = re.sub(r"_+", "_", normalized)

        if not normalized:
            raise ValueError("A column name became empty after normalization.")

        if normalized[0].isdigit():
            normalized = f"col_{normalized}"

        return normalized

    @classmethod
    def _validate_path(cls, path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {path}")

        if path.suffix.lower() not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Only CSV files are supported. Got: {path.suffix}")
