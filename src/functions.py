import pandas as pd
import json
# Method 1: Create a flattened DataFrame with all data
def create_stocks_dataframe(json_data):
    """Convert JSON stock data to pandas DataFrame"""
    
    all_rows = []
    
    for stock in json_data['stocks']:
        stock_name = stock['name']
        stock_symbol = stock['actual_symbol_used']
        
        for price_data in stock['monthly_prices']:
            row = {
                'stock_name': stock_name,
                'symbol': stock_symbol,
                'date': price_data['date'],
                'year': price_data['year'],
                'month': price_data['month'],
                'closing_price': price_data['closing_price']
            }
            all_rows.append(row)
    
    df = pd.DataFrame(all_rows)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(['stock_name', 'date']).reset_index(drop=True)
    
    return df

# Method 2: Create separate DataFrames for different views
def create_multiple_dataframes(json_data):
    """Create multiple DataFrames for different perspectives"""
    
    # 1. Main DataFrame with all price data
    price_df = create_stocks_dataframe(json_data)
    
    # 2. Stock metadata DataFrame
    metadata_rows = []
    for stock in json_data['stocks']:
        metadata_rows.append({
            'stock_name': stock['name'],
            'symbol': stock['actual_symbol_used'],
            'requested_symbols': ', '.join(stock['requested_symbols']),
            'data_points': stock['data_points'],
            'date_range_start': stock['date_range']['start'],
            'date_range_end': stock['date_range']['end']
        })
    
    metadata_df = pd.DataFrame(metadata_rows)
    
    # 3. Pivot table: Dates as index, stocks as columns
    pivot_df = price_df.pivot_table(
        index='date',
        columns='stock_name',
        values='closing_price'
    )
    
    # 
    return {
        'price_data': price_df,
        'stock_metadata': metadata_df,
        'pivot_table': pivot_df
    }