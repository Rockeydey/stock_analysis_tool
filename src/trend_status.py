"""Utilities for computing stock trend status metrics in DuckDB."""

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


def _ensure_trend_status_table(
    conn: duckdb.DuckDBPyConnection,
    table_name: str = "tbl_trend_status",
) -> None:
    """Create the trend status table if it does not already exist."""
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            stock_id BIGINT,
            stock_name VARCHAR,
            symbol VARCHAR PRIMARY KEY,
            coefficient DOUBLE,
            r_square DOUBLE,
            rmse DOUBLE,
            status VARCHAR,
            refreshed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def _compute_linear_metrics(
    stock_df: pd.DataFrame,
    date_col: str,
    price_col: str,
    forecast_horizon: int = 180,
) -> tuple[float | None, float | None, float | None, float | None]:
    """Compute slope, R-squared, RMSE, and forecasted price for a stock series."""
    working_df = stock_df.copy()
    working_df[date_col] = pd.to_datetime(working_df[date_col], errors="coerce")
    working_df[price_col] = pd.to_numeric(working_df[price_col], errors="coerce")
    working_df = working_df.dropna(subset=[date_col, price_col]).sort_values(date_col)

    if len(working_df) < 2:
        return None, None, None, None

    y = working_df[price_col].to_numpy(dtype=float)
    x = np.arange(len(y), dtype=float)

    coefficients = np.polyfit(x, y, 1)
    slope = float(coefficients[0])
    linear_fit = np.poly1d(coefficients)
    fitted = linear_fit(x)

    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    ss_res = float(np.sum((y - fitted) ** 2))
    r_square = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
    rmse = float(np.sqrt(np.mean((y - fitted) ** 2)))

    if forecast_horizon < 1:
        forecast_horizon = 1
    forecast_index = len(y) + forecast_horizon - 1
    forecast_price = float(linear_fit(forecast_index))

    return slope, float(r_square), rmse, forecast_price


def _classify_status(
    current_price: float | None,
    forecast_price: float | None,
    threshold_pct: float = 0.05,
) -> str:
    """Classify as premium, discount, or at_par using a +-threshold around forecast."""
    if current_price is None or forecast_price is None:
        return "at_par"

    if np.isnan(current_price) or np.isnan(forecast_price):
        return "at_par"

    upper = forecast_price * (1 + threshold_pct)
    lower = forecast_price * (1 - threshold_pct)

    if current_price > upper:
        return "premium"
    if current_price < lower:
        return "discount"
    return "at_par"


def upsert_trend_status_for_symbol(
    conn: duckdb.DuckDBPyConnection,
    symbol_name: str,
    source_table: str = "stock_data",
    todays_table: str = "todays_data",
    target_table: str = "tbl_trend_status",
    forecast_horizon: int = 180,
    threshold_pct: float = 0.05,
) -> dict[str, Any]:
    """Create or update one row in tbl_trend_status for the given symbol."""
    _ensure_trend_status_table(conn, target_table)

    stock_data = get_table_data(conn, source_table)
    symbol_df = stock_data[stock_data["symbol"] == symbol_name].copy()
    if symbol_df.empty:
        raise ValueError(f"No rows found in {source_table} for symbol: {symbol_name}")

    date_col = _pick_column(symbol_df.columns, ["quote_date", "trade_date", "date"])
    price_col = _pick_column(symbol_df.columns, ["adj_close", "close", "closing_price"])

    if date_col is None or price_col is None:
        raise ValueError(
            "Missing required columns for trend calculation. "
            f"Need date in [quote_date, trade_date, date] and price in [adj_close, close, closing_price]. "
            f"Available columns: {list(symbol_df.columns)}"
        )

    symbol_df[date_col] = pd.to_datetime(symbol_df[date_col], errors="coerce")
    symbol_df = symbol_df.sort_values(date_col)
    latest_row = symbol_df.iloc[-1]

    stock_id_col = _pick_column(symbol_df.columns, ["stock_id", "id"])
    stock_name_col = _pick_column(symbol_df.columns, ["stock_name", "company_name", "name"])

    stock_id = int(latest_row[stock_id_col]) if stock_id_col is not None and pd.notna(latest_row[stock_id_col]) else None
    stock_name = (
        str(latest_row[stock_name_col])
        if stock_name_col is not None and pd.notna(latest_row[stock_name_col])
        else symbol_name
    )

    coefficient, r_square, rmse, forecast_price = _compute_linear_metrics(
        stock_df=symbol_df,
        date_col=date_col,
        price_col=price_col,
        forecast_horizon=forecast_horizon,
    )

    todays_data = get_table_data(conn, todays_table)
    todays_symbol_df = todays_data[todays_data["symbol"] == symbol_name].copy()

    current_price_col = _pick_column(todays_symbol_df.columns, ["current_price", "adj_close", "close"]) if not todays_symbol_df.empty else None
    current_price: float | None = None

    if not todays_symbol_df.empty and current_price_col is not None:
        todays_symbol_df["_date"] = pd.to_datetime(
            todays_symbol_df[_pick_column(todays_symbol_df.columns, ["quote_date", "trade_date", "date"])],
            errors="coerce",
        ) if _pick_column(todays_symbol_df.columns, ["quote_date", "trade_date", "date"]) is not None else pd.NaT

        if "_date" in todays_symbol_df.columns and todays_symbol_df["_date"].notna().any():
            latest_today_row = todays_symbol_df.sort_values("_date").iloc[-1]
        else:
            latest_today_row = todays_symbol_df.iloc[-1]

        raw_current = pd.to_numeric(pd.Series([latest_today_row[current_price_col]]), errors="coerce").iloc[0]
        if pd.notna(raw_current):
            current_price = float(raw_current)

    status = _classify_status(
        current_price=current_price,
        forecast_price=forecast_price,
        threshold_pct=threshold_pct,
    )

    conn.execute(
        f"""
        INSERT INTO {target_table} (
            stock_id,
            stock_name,
            symbol,
            coefficient,
            r_square,
            rmse,
            status,
            refreshed_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, now())
        ON CONFLICT(symbol) DO UPDATE SET
            stock_id = excluded.stock_id,
            stock_name = excluded.stock_name,
            coefficient = excluded.coefficient,
            r_square = excluded.r_square,
            rmse = excluded.rmse,
            status = excluded.status,
            refreshed_at = now()
        """,
        [
            stock_id,
            stock_name,
            symbol_name,
            coefficient,
            r_square,
            rmse,
            status,
        ],
    )

    return {
        "symbol": symbol_name,
        "stock_id": stock_id,
        "stock_name": stock_name,
        "coefficient": coefficient,
        "r_square": r_square,
        "rmse": rmse,
        "status": status,
    }


def refresh_trend_status_for_all_symbols(
    conn: duckdb.DuckDBPyConnection,
    source_table: str = "stock_data",
    todays_table: str = "todays_data",
    target_table: str = "tbl_trend_status",
    forecast_horizon: int = 180,
    threshold_pct: float = 0.05,
) -> dict[str, Any]:
    """Refresh tbl_trend_status for all symbols in stock_data."""
    _ensure_trend_status_table(conn, target_table)

    stock_data = get_table_data(conn, source_table)
    if stock_data.empty:
        return {
            "source_table": source_table,
            "todays_table": todays_table,
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
            upsert_trend_status_for_symbol(
                conn=conn,
                symbol_name=symbol_name,
                source_table=source_table,
                todays_table=todays_table,
                target_table=target_table,
                forecast_horizon=forecast_horizon,
                threshold_pct=threshold_pct,
            )
            updated_rows += 1
        except Exception as exc:
            failed_symbols.append({"symbol": symbol_name, "error": str(exc)})

    return {
        "source_table": source_table,
        "todays_table": todays_table,
        "target_table": target_table,
        "processed_symbols": len(unique_symbols),
        "updated_rows": updated_rows,
        "failed_symbols": failed_symbols,
    }
