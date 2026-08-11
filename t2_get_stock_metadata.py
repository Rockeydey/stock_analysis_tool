#############################################################################################
# Script to fetch monthly closing prices for stocks over the last 10 years                  #
# and save the data in JSON format.                                                         #
#                                                                                           #
# Steps:                                                                                    #
# 1. run bse_nse_monthly_closing_2.py to get monthly closing prices and save as JSON.      #
# 2. Run this script to process the JSON data and generate stock metadata and yearwise      #
# 3. Specify the JSON file path & Cut off % in dir.py                                       #
# Outputs:                                                                                  #
# - stock_metadata.csv: Metadata for each stock including trend, direction, returns, etc.   #
#############################################################################################

import pandas as pd
import json
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from src.yearwise_price_change_summary import get_historical_prices
from dir import stocks_historical_data

# custom functions
from src.functions import create_stocks_dataframe
from src.regression import calculate_trend
from src.prepare_data import prepare_stock_data
from src.return_calculate import calculate_returns
from src.price_status import calculate_price_status
from dir import discount_threshold # User input for filtering stocks


# Load JSON data from file
with open(stocks_historical_data, 'r') as f:
    json_data_loaded = json.load(f)

# Create the DataFrames
price_df = create_stocks_dataframe(json_data_loaded)

unique_stock_names = price_df['stock_name'].unique()

stock_metadata = pd.DataFrame() # Initialize empty DataFrame to hold metadata
stock_yearwise_price = pd.DataFrame() #Initialize empty dataframe to hold yearwise stock summary


for stock_name in unique_stock_names:
    stock_df = price_df[price_df['stock_name'] == stock_name].copy()
    # Convert dates to numeric values for linear regression
    x = np.arange(len(stock_df))
    y = stock_df['closing_price'].values

    # Fit a linear regression line
    trend_slope, trend_intercept = calculate_trend(stock_df['closing_price'].values)

    # Determine forecast direction
    get_direction = "up" if trend_slope > 0 else "down"
    current_price = stock_df['closing_price'].iloc[-1]
    forecasted_price = trend_slope * len(stock_df) + trend_intercept

    # Determine price status: tag as 'premium', 'at par', or 'discount'
    get_trend = calculate_price_status(current_price, forecasted_price, discount_threshold=discount_threshold, precision=2)

    data_dict = prepare_stock_data(
        price_df=stock_df,
        stock_name=stock_name,
        date_col='date',
        price_col='closing_price',
        name_col='stock_name')
    
    # Call the function
    result_df, simplified_df = get_historical_prices(data_dict)
    simplified_df = calculate_returns(simplified_df)
    roi_numeric = pd.to_numeric(
	simplified_df['ROI(in pct)'].astype(str).str.rstrip('%').replace({'-': np.nan, '': np.nan}))

    stock_yearwise_price = pd.concat([stock_yearwise_price, simplified_df.assign(stock_name=stock_name)], ignore_index=True)
    median_return = np.nanmedian(roi_numeric)


    # Extract current return with error handling
    latest_roi = simplified_df[simplified_df['Years Back']=='Latest']['ROI(in pct)'].values
    if len(latest_roi) > 0:
        roi_str = str(latest_roi[0]).rstrip('%')
        current_return = float(roi_str) if roi_str and roi_str != '-' else np.nan
    else:
        current_return = np.nan


    # Store metadata
    stock_metadata = pd.concat([stock_metadata, pd.DataFrame({
        'stock_name': [stock_name],
        'direction': [get_direction],
        'trend': [get_trend],
        'median_return': [float(median_return)],
        'current_return': [current_return],
        'current_price': [current_price],
        'forecasted_price': [float(forecasted_price)]
    })], ignore_index=True)

    stock_metadata.to_csv('./output/stock_metadata.csv', index=False)
    stock_yearwise_price.to_csv('./output/stock_yearwise_price.csv', index=False)
    print(f"stock metadata saved in this location: ./output/stock_metadata.csv")

if __name__ == "__main__":
    print(stock_metadata)
    print(stock_yearwise_price)
    ...
