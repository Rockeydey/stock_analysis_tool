import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, List

def prepare_stock_data(
    price_df: pd.DataFrame,
    stock_name: str,
    date_col: str = 'date',
    price_col: str = 'closing_price',
    name_col: str = 'stock_name'
) -> Dict:
    """
    Prepare and filter stock data for a specific stock.
    
    Parameters:
    -----------
    price_df : pd.DataFrame
        DataFrame containing stock price data
    stock_name : str
        Name of the stock to filter for
    date_col : str, default='date'
        Name of the date column
    price_col : str, default='closing_price'
        Name of the closing price column
    name_col : str, default='stock_name'
        Name of the stock name column
    
    Returns:
    --------
    dict : Dictionary containing prepared data and metadata
    """
    # Filter data for the specific stock
    result_df = price_df[price_df[name_col] == stock_name].copy()
    
    if result_df.empty:
        raise ValueError(f"No data found for stock: {stock_name}")
    
    # Ensure date column is datetime type
    result_df[date_col] = pd.to_datetime(result_df[date_col])
    
    # Sort by date to ensure chronological order
    result_df = result_df.sort_values(date_col)
    
    # Create a DataFrame with date as index for easier lookup
    price_series = result_df.set_index(date_col)[price_col]
    
    # Get metadata
    today = datetime.now()
    earliest_date = result_df[date_col].min()
    latest_date = result_df[date_col].max()
    # latest_price = result_df.iloc[-1][price_col]
    latest_price = result_df[result_df[date_col] == latest_date][price_col].iloc[0]
    
    # Calculate how many years of data we have
    years_of_data = today.year - earliest_date.year
    
    # Create lists to store results - starting with latest date
    years_back_list = ['Latest']  # Start with 'Latest' for current price
    lookup_dates = [latest_date]
    closing_prices = [latest_price]
    target_dates_list = [today]
    days_differences = [0]
    
    # Prepare the return dictionary
    data_dict = {
        'filtered_df': result_df,
        'price_series': price_series,
        'stock_name': stock_name,
        'earliest_date': earliest_date,
        'latest_date': latest_date,
        'latest_price': latest_price,
        'years_of_data': years_of_data,
        'years_back_list': years_back_list,
        'lookup_dates': lookup_dates,
        'closing_prices': closing_prices,
        'target_dates_list': target_dates_list,
        'days_differences': days_differences,
        'today': today
    }
    
    return data_dict

if __name__ == "__main__":
    # Example usage
    sample_data = {
        'date': ['2020-01-01', '2021-01-01', '2022-01-01', '2023-01-01'],
        'closing_price': [100, 110, 120, 130],
        'stock_name': ['ABC Corp'] * 4
    }
    price_df = pd.DataFrame(sample_data)
    
    stock_data = prepare_stock_data(price_df, stock_name='ABC Corp')
    print(stock_data)