from pathlib import Path

import pandas as pd
import pytest

from src.data_loader import DataLoader


@pytest.fixture
def loader():
    return DataLoader()


def test_load_csv_reads_valid_file(loader, tmp_path):
    csv_file = tmp_path / "sales.csv"
    csv_file.write_text(
        "Product ID,Revenue,Product Name\n1,10.5,Phone\n2,20.0,Laptop\n",
        encoding="utf-8",
    )

    df = loader.load_csv(csv_file)

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["product_id", "revenue", "product_name"]
    assert len(df) == 2


def test_load_csv_raises_for_missing_file(loader):
    with pytest.raises(FileNotFoundError, match="CSV file not found"):
        loader.load_csv("missing_file.csv")


def test_load_csv_raises_for_non_csv_extension(loader, tmp_path):
    txt_file = tmp_path / "sales.txt"
    txt_file.write_text("a,b\n1,2\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Only CSV files are supported"):
        loader.load_csv(txt_file)


def test_load_csv_raises_for_empty_csv(loader, tmp_path):
    empty_csv = tmp_path / "empty.csv"
    empty_csv.write_text("", encoding="utf-8")

    with pytest.raises((ValueError, pd.errors.EmptyDataError)):
        loader.load_csv(empty_csv)


def test_normalize_column_name_basic(loader):
    assert loader.normalize_column_name("Product Name") == "product_name"


def test_normalize_column_name_removes_special_characters(loader):
    assert loader.normalize_column_name("Revenue ($)") == "revenue"


def test_normalize_column_name_prefixes_digit_start(loader):
    assert loader.normalize_column_name("2026 Sales") == "col_2026_sales"


def test_normalize_column_name_raises_when_empty_after_normalization(loader):
    with pytest.raises(ValueError, match="became empty after normalization"):
        loader.normalize_column_name("!!!")


def test_load_csv_raises_for_duplicate_columns_after_normalization(loader, tmp_path):
    csv_file = tmp_path / "dup.csv"
    csv_file.write_text(
        "Product Name,Product-Name\nPhone,Phone\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate column names detected"):
        loader.load_csv(csv_file)


def test_preview_rows_returns_limited_rows(loader, tmp_path):
    csv_file = tmp_path / "sales.csv"
    csv_file.write_text(
        "id,name\n1,A\n2,B\n3,C\n",
        encoding="utf-8",
    )

    preview = loader.preview_rows(csv_file, n=2)

    assert isinstance(preview, pd.DataFrame)
    assert len(preview) == 2
    assert list(preview.columns) == ["id", "name"]
