from __future__ import annotations

import sqlite3
from pathlib import Path

from .data_loader import DataLoader
from .schema_manager import SchemaManager
from .validator import SQLValidator
from .query_service import QueryService
from .llm_adapter import build_llm_adapter


DB_PATH = Path("data/app.db")


class CLIApp:
    def __init__(self) -> None:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(DB_PATH)
        self.loader = DataLoader()
        self.schema_manager = SchemaManager()
        self.validator = SQLValidator()
        self.llm_adapter = build_llm_adapter()
        self.query_service = QueryService(
            conn=self.conn,
            validator=self.validator,
            llm_adapter=self.llm_adapter,
        )

    def run(self) -> None:
        print("LLM Data System")
        print(f"Connected to SQLite database: {DB_PATH}")

        while True:
            print("\nChoose an option:")
            print("1. Load CSV file")
            print("2. Run validated SQL query")
            print("3. Run natural language query")
            print("4. List tables")
            print("5. Show schema")
            print("6. Exit")

            choice = input("> ").strip()

            try:
                if choice == "1":
                    self.load_csv_flow()
                elif choice == "2":
                    self.sql_query_flow()
                elif choice == "3":
                    self.nl_query_flow()
                elif choice == "4":
                    self.list_tables_flow()
                elif choice == "5":
                    self.show_schema_flow()
                elif choice == "6":
                    print("Goodbye.")
                    break
                else:
                    print("Invalid option. Please choose 1-6.")
            except Exception as exc:
                print(f"Error: {exc}")
                self.schema_manager.log_error(str(exc))

        self.conn.close()

    def load_csv_flow(self) -> None:
        file_path = input("Enter CSV file path: ").strip()
        requested_table_name = input("Enter desired table name: ").strip().lower()

        if not requested_table_name:
            raise ValueError("Table name cannot be empty.")

        df = self.loader.load_csv(file_path)
        inferred_schema = self.schema_manager.infer_schema(df)
        compatible_table = self.schema_manager.find_compatible_table(self.conn, inferred_schema)

        if compatible_table:
            print(f"Compatible existing table found: {compatible_table}")
            choice = input("Append to this table? (y/n): ").strip().lower()

            if choice == "y":
                self._insert_rows(compatible_table, df)
                print(f"Inserted {len(df)} rows into '{compatible_table}'.")
                return

        existing_tables = self.schema_manager.get_existing_tables(self.conn)
        target_table = requested_table_name

        if target_table in existing_tables:
            print(f"Table '{target_table}' already exists but schema does not match.")
            conflict_choice = input("Type 'rename' to use a new name or 'skip' to cancel: ").strip().lower()

            if conflict_choice == "skip":
                print("Load canceled.")
                return

            if conflict_choice != "rename":
                raise ValueError("Invalid conflict option. Use 'rename' or 'skip'.")

            target_table = input("Enter new table name: ").strip().lower()
            if not target_table:
                raise ValueError("New table name cannot be empty.")

        self.schema_manager.create_table(self.conn, target_table, inferred_schema)
        self._insert_rows(target_table, df)
        print(f"Created table '{target_table}' and inserted {len(df)} rows.")

    def sql_query_flow(self) -> None:
        schema = self._build_schema_snapshot()

        if not schema:
            print("No tables available. Load a CSV first.")
            return

        sql_query = input("Enter a SELECT query: ").strip()
        result = self.query_service.execute_validated_sql(sql_query, schema)
        print("\nGenerated / Submitted SQL:")
        print(result["sql"])
        print("\nResults:")
        print(self.query_service.format_result(result))

    def nl_query_flow(self) -> None:
        schema = self._build_schema_snapshot()

        if not schema:
            print("No tables available. Load a CSV first.")
            return

        user_request = input("Ask a question about your data: ").strip()
        result = self.query_service.process_natural_language_query(user_request, schema)

        print("\nGenerated SQL:")
        print(result["sql"])
        print("\nResults:")
        print(self.query_service.format_result(result))

    def list_tables_flow(self) -> None:
        tables = self.query_service.list_tables()

        if not tables:
            print("No tables found.")
            return

        print("\nTables:")
        for table in tables:
            print(f"- {table}")

    def show_schema_flow(self) -> None:
        schema = self._build_schema_snapshot()

        if not schema:
            print("No tables found.")
            return

        print("\nDatabase schema:")
        for table_name, columns in schema.items():
            print(f"\n{table_name}")
            for column_name, column_type in columns.items():
                print(f"  - {column_name}: {column_type}")

    def _build_schema_snapshot(self) -> dict[str, dict[str, str]]:
        schema: dict[str, dict[str, str]] = {}

        for table_name in self.schema_manager.get_existing_tables(self.conn):
            schema[table_name] = self.schema_manager.get_table_schema(self.conn, table_name)

        return schema

    def _insert_rows(self, table_name: str, df) -> None:
        columns = list(df.columns)
        placeholders = ", ".join(["?"] * len(columns))
        column_sql = ", ".join(columns)

        sql = f"INSERT INTO {table_name} ({column_sql}) VALUES ({placeholders})"
        records = [tuple(row) for row in df.itertuples(index=False, name=None)]

        self.conn.executemany(sql, records)
        self.conn.commit()


def main() -> None:
    app = CLIApp()
    app.run()


if __name__ == "__main__":
    main()
