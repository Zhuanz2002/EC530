# LLM Data System

A modular Python + SQLite data system that loads structured CSV data into a database and supports both validated SQL queries and natural-language queries through an LLM interface.

## Overview

This project implements a safe data-query pipeline with two main goals:

1. Load structured CSV data into SQLite
2. Let users query the data using either:
   - direct SQL input
   - natural-language input translated into SQL by an LLM adapter

The system is designed around modular architecture, validation, and testability.

## Main Components

### 1. CLI Interface
The command-line interface is the entry point for the user.

Responsibilities:
- display menu options
- receive user input
- call the appropriate service functions

Important design rule:
- the CLI does **not** directly access the database

### 2. DataLoader
The `DataLoader` is responsible for reading CSV files safely.

Responsibilities:
- validate file path and extension
- load CSV files with pandas
- normalize column names
- detect invalid inputs such as empty files or duplicate normalized column names

### 3. SchemaManager
The `SchemaManager` is responsible for understanding and managing database structure.

Responsibilities:
- infer SQLite schema from DataFrame columns
- inspect existing tables
- read schema using `PRAGMA table_info()`
- compare schemas to decide append vs create
- generate `CREATE TABLE` statements
- add `id INTEGER PRIMARY KEY AUTOINCREMENT` for new tables

### 4. SQLValidator
The `SQLValidator` protects the database before execution.

Responsibilities:
- allow only `SELECT` queries
- reject unknown tables
- reject unknown columns
- block dangerous multi-statement patterns

### 5. LLMAdapter
The `LLMAdapter` translates natural language into SQL.

Responsibilities:
- accept user request and schema context
- generate SQL text only
- never execute SQL directly

This project includes:
- `MockLLMAdapter` for local development and testing
- optional OpenAI-backed adapter if an API key is provided

### 6. QueryService
The `QueryService` is the control layer for query execution.

Responsibilities:
- receive SQL or natural-language requests
- call the LLM adapter if needed
- validate SQL before execution
- execute validated SQL
- format results for display

## Architecture

The system has two independent flows.

### Data Ingestion Flow
CLI -> DataLoader -> SchemaManager -> SQLite

### Query Flow
CLI -> QueryService -> LLMAdapter -> SQLValidator -> SQLite

This design ensures separation of concerns and keeps the system testable and maintainable.

## Project Structure

```text
.
├── .github/
│   └── workflows/
│       └── ci.yml
├── src/
│   ├── __init__.py
│   ├── cli.py
│   ├── data_loader.py
│   ├── schema_manager.py
│   ├── query_service.py
│   ├── llm_adapter.py
│   └── validator.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_data_loader.py
│   ├── test_schema_manager.py
│   ├── test_query_service.py
│   ├── test_llm_adapter.py
│   └── test_validator.py
├── data/
├── main.py
├── requirements.txt
├── README.md
└── .gitignore