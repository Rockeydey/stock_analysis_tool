# stock_analysis_tool

## Priority Return Metrics Logic

This project computes two return metrics for each stock symbol:

1. median_lifetime_return
2. current_yr_return

Both are calculated from yearly anchor prices:

1. first_close_of_year = first available close in that year (earliest date present in data)
2. last_close_of_year = last available close in that year (latest date present in data)

Important: These are based on available dates in the dataset. They do not need to be Jan 1 and Dec 31.

### Yearly Return Formula

yearly_return(%) = ((last_close_of_year - first_close_of_year) / first_close_of_year) * 100

### Data Handling Rules

1. Convert date and close columns to valid types.
2. Drop rows where date or close is invalid.
3. Sort by date ascending.
4. If multiple rows exist for the same date, keep the last close for that date.
5. Group by calendar year.
6. For each year, use:
	- first close in that year as first_close_of_year
	- last close in that year as last_close_of_year
7. Exclude years where first_close_of_year is 0.

### What Each Metric Means

1. median_lifetime_return:
	- Compute yearly_return for all valid years.
	- Take the median of those yearly returns.

2. current_yr_return:
	- Find the latest year present in data.
	- Return that year's yearly_return.

### Example With Dates

Assume one stock has these closes:

- 2024-01-03: 100
- 2024-12-30: 125
- 2025-01-07: 130
- 2025-08-14: 140

For 2024:
- first_close_of_year = 100 (on 2024-01-03)
- last_close_of_year = 125 (on 2024-12-30)
- yearly_return = ((125 - 100) / 100) * 100 = 25%

For 2025:
- first_close_of_year = 130 (on 2025-01-07)
- last_close_of_year = 140 (on 2025-08-14)
- yearly_return = ((140 - 130) / 130) * 100 = 7.6923%

So:
- current_yr_return = 7.6923% (latest year = 2025)
- median_lifetime_return = median of [25, 7.6923] = 16.34615%

## How Median Logic Is Used In This Script

The median calculation is done in src/priority_mapping.py inside the function _compute_yearly_anchor_returns.

Flow used by the script:

1. Build yearly_return values for each valid year.
2. Convert those yearly returns into a list named returns.
3. Compute median_lifetime_return using NumPy median on that list.
4. Return both values as a tuple:
	- median_lifetime_return
	- current_yr_return (latest year only)

Median behavior:

1. If number of yearly returns is odd, median is the middle value after sorting.
2. If number of yearly returns is even, median is the average of the two middle values.

How this is applied to DB updates:

1. upsert_priority_for_symbol calls _compute_yearly_anchor_returns for one symbol.
2. The returned median_lifetime_return is inserted or updated in tbl_priority.
3. refresh_priority_for_all_symbols repeats the same logic symbol-by-symbol, so each row in tbl_priority gets a median based on that stock's full yearly history.

Why median is used:

Median is less sensitive to one extreme year than a simple average, so it gives a more stable central tendency for long-term yearly performance.