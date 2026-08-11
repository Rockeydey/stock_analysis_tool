from datetime import datetime
import numpy as np

# Function to find the closest available date
def find_closest_date(target_date, price_series):
    """Find the closest available date in the price series"""
    # Try exact match first
    if target_date in price_series.index:
        return target_date, price_series[target_date], 0
    
    # Find the closest date (before or after)
    try:
        # Get all dates
        all_dates = price_series.index
        
        # Calculate absolute time differences
        time_diffs = np.abs(all_dates - target_date)
        
        # Find index of minimum time difference
        closest_idx = np.argmin(time_diffs)
        closest_date = all_dates[closest_idx]
        days_diff = (closest_date - target_date).days
        
        return closest_date, price_series.iloc[closest_idx], days_diff
    except:
        return None, None, None