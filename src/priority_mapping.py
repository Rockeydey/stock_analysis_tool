"""Utilities for computing and refreshing stock priority metrics in DuckDB."""

from __future__ import annotations

from typing import Any

import duckdb
import numpy as np
import pandas as pd

from src.duck_db_utils import get_table_data


def _pick_column(columns: pd.Index, candidates: list[str]) -> str | None:
    """Return the first matching column name (case-insensitive) from candidates."""
    col_lookup = {str(col).strip().lower(): str(col) for col in columns}
    for candidate in candidates:
        match = col_lookup.get(candidate.strip().lower())
        if match is not None:
            return match
    return None


def _compute_yearly_anchor_returns(
    stock_df: pd.DataFrame,
    date_col: str,
    price_col: str,
) -> tuple[float | None, float | None, int]:
    """Compute median lifetime yearly return and current year return in percent.

    Uses calendar-year return = ((last close - first close) / first close) * 100.
    """
    if stock_df.empty:
        return None, None, 0

    working_df = stock_df.copy()
    working_df["quote_date"] = pd.to_datetime(working_df[date_col], errors="coerce")
    working_df["close"] = pd.to_numeric(working_df[price_col], errors="coerce")
    working_df = working_df.dropna(subset=["quote_date", "close"]).sort_values("quote_date")

    if working_df.empty:
        return None, None, 0

    # If multiple rows exist for the same date, keep the last observed close.
    working_df = (
        working_df.groupby("quote_date", as_index=False)["close"].last().sort_values("quote_date")
    )
    working_df["year"] = working_df["quote_date"].dt.year
    data_availability_yrs = int(working_df["year"].nunique())

    yearly_prices = working_df.groupby("year")["close"].agg(first_close="first", last_close="last")
    valid_yearly = yearly_prices[yearly_prices["first_close"] != 0].copy()

    if valid_yearly.empty:
        return None, None, data_availability_yrs

    valid_yearly["yearly_return"] = (
        (valid_yearly["last_close"] - valid_yearly["first_close"]) / valid_yearly["first_close"]
    ) * 100

    returns = valid_yearly["yearly_return"].dropna().tolist()

    if not returns:
        return None, None, data_availability_yrs

    latest_year = int(working_df["year"].max())
    current_yr_series = valid_yearly.loc[valid_yearly.index == latest_year, "yearly_return"]
    current_yr_return = float(current_yr_series.iloc[0]) if not current_yr_series.empty else None

    median_lifetime_return = float(np.median(returns))
    return median_lifetime_return, current_yr_return, data_availability_yrs


def _ensure_priority_table(conn: duckdb.DuckDBPyConnection, table_name: str = "tbl_priority") -> None:
    """Create the priority table if it does not already exist."""
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            stock_id BIGINT,
            stock_name VARCHAR,
            symbol VARCHAR PRIMARY KEY,
            median_lifetime_return DOUBLE,
            current_yr_return DOUBLE,
            data_availability_yrs INTEGER,
            refreshed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        f"""
        ALTER TABLE {table_name}
        ADD COLUMN IF NOT EXISTS data_availability_yrs INTEGER
        """
    )


def upsert_priority_for_symbol(
    conn: duckdb.DuckDBPyConnection,
    symbol_name: str,
    source_table: str = "stock_data",
    target_table: str = "tbl_priority",
) -> dict[str, Any]:
    """Create/update one row in target_table for the given symbol.

    - Creates `target_table` if it does not exist.
    - Overwrites existing values when the symbol already exists.
    - Never appends duplicate rows for the same symbol.
    """
    _ensure_priority_table(conn, target_table)

    stock_data = get_table_data(conn, source_table)
    symbol_df = stock_data[stock_data["symbol"] == symbol_name].copy()

    if symbol_df.empty:
        raise ValueError(f"No rows found in {source_table} for symbol: {symbol_name}")

    date_col = _pick_column(symbol_df.columns, ["quote_date", "trade_date", "date"])
    price_col = _pick_column(symbol_df.columns, ["close", "adj_close"])

    if date_col is None or price_col is None:
        raise ValueError(
            "Missing required columns for return calculation. "
            f"Need date in [quote_date, trade_date, date] and price in [close, adj_close]. "
            f"Available columns: {list(symbol_df.columns)}"
        )

    symbol_df[date_col] = pd.to_datetime(symbol_df[date_col], errors="coerce")
    symbol_df = symbol_df.sort_values(date_col)
    latest_row = symbol_df.iloc[-1]

    stock_id_col = _pick_column(symbol_df.columns, ["stock_id", "id"])
    stock_name_col = _pick_column(symbol_df.columns, ["company_name", "stock_name", "name"])

    stock_id = int(latest_row[stock_id_col]) if stock_id_col is not None and pd.notna(latest_row[stock_id_col]) else None
    stock_name = (
        str(latest_row[stock_name_col])
        if stock_name_col is not None and pd.notna(latest_row[stock_name_col])
        else symbol_name
    )

    median_lifetime_return, current_yr_return, data_availability_yrs = _compute_yearly_anchor_returns(
        stock_df=symbol_df,
        date_col=date_col,
        price_col=price_col,
    )

    conn.execute(
        f"""
        INSERT INTO {target_table} (
            stock_id,
            stock_name,
            symbol,
            median_lifetime_return,
            current_yr_return,
            data_availability_yrs,
            refreshed_at
        )
        VALUES (?, ?, ?, ?, ?, ?, now())
        ON CONFLICT(symbol) DO UPDATE SET
            stock_id = excluded.stock_id,
            stock_name = excluded.stock_name,
            median_lifetime_return = excluded.median_lifetime_return,
            current_yr_return = excluded.current_yr_return,
            data_availability_yrs = excluded.data_availability_yrs,
            refreshed_at = now()
        """,
        [
            stock_id,
            stock_name,
            symbol_name,
            median_lifetime_return,
            current_yr_return,
            data_availability_yrs,
        ],
    )

    return {
        "symbol": symbol_name,
        "stock_id": stock_id,
        "stock_name": stock_name,
        "median_lifetime_return": median_lifetime_return,
        "current_yr_return": current_yr_return,
        "data_availability_yrs": data_availability_yrs,
    }


def refresh_priority_for_all_symbols(
    conn: duckdb.DuckDBPyConnection,
    source_table: str = "stock_data",
    target_table: str = "tbl_priority",
) -> dict[str, Any]:
    """Refresh tbl_priority for all symbols found in source_table.

    This performs an upsert per symbol, so existing rows are overwritten and
    missing rows are inserted with no duplication.
    """
    _ensure_priority_table(conn, target_table)

    stock_data = get_table_data(conn, source_table)
    if stock_data.empty:
        return {
            "source_table": source_table,
            "target_table": target_table,
            "processed_symbols": 0,
            "updated_rows": 0,
            "failed_symbols": [],
        }

    if "symbol" not in stock_data.columns:
        raise ValueError(f"Column 'symbol' not found in {source_table}")

    unique_symbols = (
        stock_data["symbol"]
        .dropna()
        .astype(str)
        .str.strip()
        .loc[lambda s: s != ""]
        .drop_duplicates()
        .tolist()
    )

    failed_symbols: list[dict[str, str]] = []
    updated_rows = 0

    for symbol_name in unique_symbols:
        try:
            upsert_priority_for_symbol(
                conn=conn,
                symbol_name=symbol_name,
                source_table=source_table,
                target_table=target_table,
            )
            updated_rows += 1
        except Exception as exc:  # Continue refresh if one symbol fails.
            failed_symbols.append({"symbol": symbol_name, "error": str(exc)})

    return {
        "source_table": source_table,
        "target_table": target_table,
        "processed_symbols": len(unique_symbols),
        "updated_rows": updated_rows,
        "failed_symbols": failed_symbols,
    }
