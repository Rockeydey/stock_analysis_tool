import pandas as pd
from datetime import datetime, timedelta
from src.closest_date import find_closest_date


def get_historical_prices(data_dict):
    """
    Retrieve historical prices for each year back from today until data runs out.
    
    Args:
        data_dict (dict): Dictionary containing price data and metadata with keys:
            - 'years_of_data': Number of years of available data
            - 'today': Current date (datetime object)
            - 'earliest_date': Earliest date in the dataset (datetime object)
            - 'price_series': DataFrame with price data (columns: 'Date', 'Close')
            - 'years_back_list': Empty list to store years back values
            - 'target_dates_list': Empty list to store target dates
            - 'lookup_dates': Empty list to store actual lookup dates
            - 'closing_prices': Empty list to store closing prices
            - 'days_differences': Empty list to store day differences
    
    Returns:
        tuple: (result_df, simplified_df) - Two DataFrames with historical price data
            or (None, None) if no data was found
    """
    
    # Get prices for each year back until we run out of data
    for years_back in range(1, data_dict['years_of_data'] + 2):  # +2 to include partial years
        # Calculate the target date (years back from today)
        target_date = data_dict['today'] - timedelta(days=365 * years_back)
        
        # Check if target date is before earliest date in dataset
        if target_date < data_dict['earliest_date']:
            print(f"\nStopping at {years_back-1} years back. Target date {target_date.date()} is before earliest data ({data_dict['earliest_date'].date()})")
            break
        
        # Find the closest available date and price
        actual_date, price, days_diff = find_closest_date(target_date, data_dict['price_series'])
        
        if actual_date is not None and price is not None:
            data_dict['years_back_list'].append(years_back)
            data_dict['target_dates_list'].append(target_date)
            data_dict['lookup_dates'].append(actual_date)
            data_dict['closing_prices'].append(price)
            data_dict['days_differences'].append(days_diff)
        else:
            print(f"No data found for {years_back} years back ({target_date.date()})")
    
    # Create the result DataFrame
    if data_dict['years_back_list']:  # Check if we found any data
        result_df = pd.DataFrame({
            'Years Back': data_dict['years_back_list'],
            'Target Date': data_dict['target_dates_list'],
            'Actual Date': data_dict['lookup_dates'],
            'Closing Price': data_dict['closing_prices'],
            'Days Difference': data_dict['days_differences']
        })
        
        # Create simplified version with just Years Back, Actual Date, and Closing Price
        simplified_df = result_df[['Years Back', 'Actual Date', 'Closing Price']].rename(
            columns={'Actual Date': 'lookup_date', 'Closing Price': 'Closing price'}
        )
        
        return result_df, simplified_df
    else:
        print("No historical price data found.")
        return None, None