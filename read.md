Project: TRANSFORMERS AND RECTIFIERS (INDIA) LIMITED - Data Fetcher

Overview
--------
This repository contains a single Python script, `bse_nse_2.py`, which provides a compact utility — `IndianStockDataFetcher` — to fetch, format, display and save stock data for "Transformers and Rectifiers (India) Limited" (TARIL). The script attempts multiple data sources in order of reliability and gracefully falls back when a method fails.

Purpose
-------
- Collect price, volume and fundamental metrics for TARIL.
- Provide structured output to console, CSV and (optionally) Excel with basic formatting.
- Use multiple data sources (Yahoo Finance via `yfinance`, NSE API, BSE API, Moneycontrol scraping) so the script remains resilient.

Architecture & Design
---------------------
- Single-class design: `IndianStockDataFetcher` encapsulates functionality.
  - Constructor sets up a `requests.Session` and common headers used for web requests.
- Major responsibilities (methods):
  - `get_all_data_yfinance()` — Primary method using `yfinance` to fetch full dataset (prices, market cap, ratios, timestamps).
  - `get_nse_data_alternative(symbol)` and helpers (`parse_nse_alternative`, `get_nse_data_fallback`) — Query NSE endpoints and fall back to web scraping if needed.
  - `get_bse_data_alternative(scrip_code)` and helpers (`parse_bse_alternative`, `parse_bse_text`, `get_bse_data_fallback`) — Query BSE endpoints and fall back to scraping.
  - `get_financial_data(company_name)` — Orchestrates retrieval of ratios and fundamental metrics via Moneycontrol and a fallback to Yahoo Finance.
  - `display_data(data)` — Nicely prints grouped categories to console.
  - `save_to_csv(data, filename)` — Exports results to CSV using `pandas`.
  - `save_to_excel(data, filename)` — Exports results to Excel using `pandas` with `openpyxl` engine and applies header formatting and column width adjustments.
- Helper formatters:
  - `format_number(num)` — Formats large numeric values using suffixes (K, M, B).
  - `format_market_cap(market_cap)` — Formats market capitalization into ₹ with appropriate suffixes.

Data Flow (high-level)
----------------------
1. `main()` instantiates `IndianStockDataFetcher`.
2. It first calls `get_all_data_yfinance()` — if successful, the returned dictionary is printed and saved.
3. If `yfinance` fails or returns incomplete results, `main()` tries alternatives in order: `get_nse_data_alternative`, `get_bse_data_alternative`, and `get_financial_data`.
4. The exporter methods write CSV always and attempt to write Excel if `openpyxl` is available.

Key Implementation Notes
------------------------
- Resilience: Each network operation is wrapped with try/except blocks and fallback logic to minimize total failure.
- `requests.Session()` is used for cookie-based endpoints (NSE) where an initial visit sets cookies required by subsequent API calls.
- `yfinance` is the preferred source for complete data because it unifies many fields; other endpoints are used when `yfinance` does not provide required fields.
- HTML scraping uses `BeautifulSoup` for fallback when official endpoints are unavailable or return unexpected payloads.

Requirements
------------
The project assumes a Python environment with the following packages (also present in `requirements.txt`):
- `requests`
- `pandas`
- `yfinance`
- `openpyxl` (optional but needed for Excel export)
- `beautifulsoup4` (only if you need scraping fallbacks)

Install (Windows PowerShell)
---------------------------
Run these commands in PowerShell:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
# If you don't have a requirements.txt, install manually:
python -m pip install requests pandas yfinance openpyxl beautifulsoup4
```

Running the script
------------------
From the project root (where `bse_nse_2.py` lives):

```powershell
python bse_nse_2.py
```

This will:
- Try `yfinance` first and print the consolidated dataset.
- Save `taril_stock_data.csv` (always) and try to save `taril_stock_data.xlsx` (only if `openpyxl` is installed).
- If `yfinance` fails, the script will attempt NSE/BSE endpoints and Moneycontrol scraping.

Excel export behavior
---------------------
- The Excel export uses `pandas.ExcelWriter(..., engine='openpyxl')` and applies a header fill color and white bold text.
- If your runtime throws `NameError: name 'openpyxl' is not defined`, ensure `openpyxl` is installed and an `import openpyxl` exists where needed. The script already includes an `import openpyxl` at top — if you removed it, add it back.

Common troubleshooting
----------------------
- Network errors: Endpoints (NSE/BSE/Moneycontrol) may block automated requests or change endpoints. Add delays and verify headers if you see HTTP 403/429.
- `yfinance` rate limits: If you receive occasional incomplete results, retry or add sleeps between calls.
- Date/Locale: Market data timestamps may be in different time zones — script uses `datetime.now()` when composing `Timestamp`.

Extending the script
--------------------
- Add command-line arguments to specify symbol(s), output paths, or toggles for which sources to use.
- Move the class into a proper package/module structure and add unit tests for the formatters and parsing functions.
- Add caching to avoid repeated API hits during debugging.

File list (important files)
--------------------------
- `bse_nse_2.py` — Main script containing `IndianStockDataFetcher` and `main()` entrypoint.
- `requirements.txt` — Python dependencies (update if you add new packages).
- `taril_stock_data.csv` — Example output generated by the script.
- `read.md` — This documentation file.

Author / Contact
----------------
- Created for local automation and quick research. Modify freely for personal use.

License
-------
- No license specified. Add one if you plan to share or distribute this code.
