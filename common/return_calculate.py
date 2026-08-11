from datetime import datetime
import pandas as pd
import numpy as np


# Function to calculate percentage returns
def calculate_returns(df):
    """
    Calculate percentage return from one year to the next
    
    Formula: Return = ((Price_previous - Price_current) / Price_current) * 100
    where Price_previous is the price from one year earlier
    """
    # Work on a copy to avoid modifying original unexpectedly
    df = df.copy()

    # Convert closing prices to numeric
    df['Closing price'] = pd.to_numeric(df['Closing price'])

    # Create a numeric column for sorting 'Years Back' robustly.
    # Map 'Latest' -> 0, integers remain as-is. Unknown values become NaN.
    def years_back_to_num(x):
        try:
            return int(x)
        except Exception:
            if str(x).strip().lower() == 'latest':
                return 0
            return np.nan

    df['years_back_num'] = df['Years Back'].apply(years_back_to_num)

    # Sort by the numeric years column (ascending: Latest (0), 1, 2, ...)
    df = df.sort_values('years_back_num').reset_index(drop=True)

    # Calculate returns
    returns = []
    for i in range(len(df)):
        if i < len(df) - 1:
            current_price = df.loc[i, 'Closing price']
            next_price = df.loc[i + 1, 'Closing price']
            # Guard against division by zero or missing prices
            if pd.notnull(current_price) and current_price != 0 and pd.notnull(next_price):
                return_pct = ((current_price - next_price) / next_price) * 100
                returns.append(f"{return_pct:.0f}")
            else:
                returns.append('-')
        else:
            # For the oldest year, we don't have a previous year to compare with
            returns.append('-')

    # Update the Return column
    df['ROI(in pct)'] = returns

    # Drop the helper column before returning
    df = df.drop(columns=['years_back_num'])

    return df