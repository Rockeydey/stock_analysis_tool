"""
DuckDB utility functions.

Updated: 12-08-2026
"""


import pandas as pd

import duckdb
from pathlib import Path

# UDFs functions
from src.load_config import load_json_config


local_config = load_json_config("config/local.json")

DB_PATH = Path(local_config["database_path"])
_CONN: duckdb.DuckDBPyConnection | None = None


def get_conn(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    """
    Get a connection to the DuckDB database.
    
    Args:
        read_only (bool): When True, force a read-only connection.

    Returns:
        duckdb.DuckDBPyConnection: A connection object to the DuckDB database.
    """
    global _CONN

    # Reuse an existing live connection to avoid file lock errors on Windows.
    if _CONN is not None:
        try:
            _CONN.execute("SELECT 1")
            return _CONN
        except Exception:
            _CONN = None

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # If another process holds a write lock, fallback to read-only so notebooks can still query.
    try:
        _CONN = duckdb.connect(str(DB_PATH), read_only=read_only)
    except duckdb.IOException as exc:
        if read_only:
            raise

        is_lock_error = "already open" in str(exc).lower() or "being used" in str(exc).lower()
        if is_lock_error and DB_PATH.exists():
            _CONN = duckdb.connect(str(DB_PATH), read_only=True)
        else:
            raise

    return _CONN


def close_conn() -> None:
    """Close the shared DuckDB connection if it is open."""
    global _CONN
    if _CONN is not None:
        try:
            _CONN.close()
        finally:
            _CONN = None


def get_db_table_names(conn: duckdb.DuckDBPyConnection) -> list[str]:
    """
    Get the names of all tables in the DuckDB database.
    
    Args:
        conn (duckdb.DuckDBPyConnection): A connection object to the DuckDB database.

    Returns:
        list[str]: A list of table names in the DuckDB database.
    """
    result = conn.execute("SHOW TABLES").fetchall()
    return [row[0] for row in result]


def get_table_data(conn: duckdb.DuckDBPyConnection, table_name: str) -> pd.DataFrame:
    """
    Get all data from a specified table in the DuckDB database as a pandas DataFrame.
    
    Args:
        conn (duckdb.DuckDBPyConnection): A connection object to the DuckDB database.
        table_name (str): The name of the table to retrieve data from.

    Returns:
        pd.DataFrame: A DataFrame containing the data from the specified table.
    """
    return conn.execute(f"SELECT * FROM {table_name}").fetch_df()



if __name__ == "__main__":
    # conn = get_conn()
    # print(f"Connected to DuckDB database at: {DB_PATH}")
    ...


