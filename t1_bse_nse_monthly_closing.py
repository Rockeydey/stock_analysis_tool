#################################################################################
# Script to fetch monthly closing prices for stocks over the last 10 years      #
# and save the data in JSON format.                                             #      
#################################################################################

import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
import json
import os

# Import stocks_name_list from dir.py
from dir import stocks_name_list

class StockMonthlyDataFetcher:
    def __init__(self):
        pass
    
    def get_monthly_closing_prices(self, symbols=None):
        """Get monthly closing prices for the last 10 years
        
        Args:
            symbols: List of ticker symbols to try
            
        Returns:
            DataFrame with monthly closing prices
        """
        try:
            # Try provided symbols or fall back to defaults
            symbols = symbols or []
            
            for symbol in symbols:
                try:
                    print(f"Trying symbol: {symbol}")
                    stock = yf.Ticker(symbol)
                    
                    # Calculate date range: last 10 years
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=365 * 10)
                    
                    # Fetch monthly data
                    hist = stock.history(start=start_date, end=end_date, interval="1mo")
                    
                    if not hist.empty and len(hist) > 0:
                        print(f"✓ Found data for {symbol}")
                        
                        # Create a clean DataFrame with just the closing prices
                        monthly_data = pd.DataFrame({
                            'Date': hist.index,
                            'Symbol': symbol,
                            'Close': hist['Close']
                        })
                        
                        # Reset index to make Date a column
                        monthly_data = monthly_data.reset_index(drop=True)
                        
                        # Add year and month columns
                        monthly_data['Year'] = monthly_data['Date'].dt.year
                        monthly_data['Month'] = monthly_data['Date'].dt.month
                        
                        # Sort by date (oldest to newest)
                        monthly_data = monthly_data.sort_values('Date')
                        
                        return monthly_data
                        
                except Exception as e:
                    print(f"  Error with {symbol}: {e}")
                    continue
            
            print("✗ Could not fetch data for any symbol")
            return None
            
        except Exception as e:
            print(f"Error fetching monthly data: {e}")
            return None
    
    def format_output_data(self, monthly_data, stock_name):
        """Format the monthly data for output"""
        if monthly_data is None or monthly_data.empty:
            return None
        
        # Create a clean output DataFrame
        output_df = pd.DataFrame({
            'Stock_Name': stock_name,
            'Symbol': monthly_data['Symbol'],
            'Date': monthly_data['Date'].dt.strftime('%Y-%m-%d'),
            'Year': monthly_data['Year'],
            'Month': monthly_data['Month'],
            'Closing_Price': monthly_data['Close'].round(2)
        })
        
        # Add latest (max) date and its closing price for convenience
        latest_row = monthly_data.iloc[-1]
        latest_date_str = latest_row['Date'].strftime('%Y-%m-%d')
        latest_price = round(float(latest_row['Close']), 2)
        output_df['Latest_Date'] = latest_date_str
        output_df['Latest_Closing_Price'] = latest_price

        return output_df
    
    def save_to_json(self, all_stocks_data, filename="collated_stocks_data.json"):
        """Save collated stocks data to JSON file"""
        if not all_stocks_data:
            print("No data to save")
            return
        
        # Ensure output directory exists
        os.makedirs('output', exist_ok=True)
        
        # Prepare JSON structure
        json_data = {
            "metadata": {
                "total_stocks": len(all_stocks_data),
                "generated_on": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "data_range_years": 10,
                "data_frequency": "monthly"
            },
            "stocks": all_stocks_data
        }
        
        # Save to JSON file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✓ Collated data saved to {filename}")
    
    def format_for_json(self, formatted_data, original_symbols):
        """Format data for JSON output"""
        if formatted_data is None or formatted_data.empty:
            return None
        
        # Get unique stock name and symbol
        stock_name = formatted_data['Stock_Name'].iloc[0]
        actual_symbol = formatted_data['Symbol'].iloc[0]
        
        # Prepare monthly data in a structured format
        monthly_prices = []
        for _, row in formatted_data.iterrows():
            monthly_prices.append({
                "date": row['Date'],
                "year": int(row['Year']),
                "month": int(row['Month']),
                "closing_price": float(row['Closing_Price'])
            })
        
        # Prepare stock data structure
        stock_data = {
            "name": stock_name,
            "requested_symbols": original_symbols,
            "actual_symbol_used": actual_symbol,
            "data_points": len(monthly_prices),
            "date_range": {
                "start": formatted_data['Date'].iloc[0],
                "end": formatted_data['Date'].iloc[-1]
            },
            "monthly_prices": monthly_prices
        }
        
        return stock_data
    
    def save_individual_json(self, stock_data, timestamp):
        """Save individual stock data to separate JSON file"""
        if stock_data is None:
            return
        
        stock_name = stock_data['name']
        safe_name = stock_name.replace(' ', '_').replace('/', '_').replace('&', 'and')
        
        # Ensure output directory exists
        os.makedirs('output/individual_stocks', exist_ok=True)
        
        # filename = f"output/individual_stocks/{safe_name}_{timestamp}.json"
        filename = f"output/individual_stocks/{safe_name}.json"

        # Prepare individual JSON structure
        individual_json = {
            "metadata": {
                "generated_on": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "data_range_years": 10,
                "data_frequency": "monthly"
            },
            "stock_data": stock_data
        }
        
        # Save to JSON file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(individual_json, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"✓ Individual JSON saved to {filename}")

def main():
    """Main function to fetch monthly closing prices for all stocks in JSON"""
    print("FETCHING MONTHLY CLOSING PRICES - LAST 10 YEARS")
    print("="*60)
    
    fetcher = StockMonthlyDataFetcher()
    
    
    
    try:
        with open(stocks_name_list, 'r', encoding='utf-8') as f:
            stocks_json = json.load(f)
            stocks_list = stocks_json.get('stocks', [])
    except Exception as e:
        print(f"Error reading {stocks_name_list}: {e}")
        print("Please create input/stocks_list.json with your stock list")
        return
    
    if not stocks_list:
        print(f"No stocks found in {stocks_name_list}")
        return
    
    # Create output directory
    os.makedirs('output', exist_ok=True)
    
    # Define output filenames
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_filename = f"output/collated_stocks_data.json"
    
    all_stocks_json_data = []  # To store all data for JSON output
    
    print(f"\nProcessing {len(stocks_list)} stock(s)...")
    
    successful_stocks = 0
    failed_stocks = 0
    
    for stock in stocks_list:
        name = stock.get('name', 'Unknown')
        symbols = stock.get('symbol', [])
        
        # Handle single symbol string or list
        if isinstance(symbols, str):
            symbols = [symbols]
        
        print(f"\n{'='*50}")
        print(f"Fetching: {name}")
        print(f"Trying symbols: {symbols}")
        
        # Get monthly closing prices
        monthly_data = fetcher.get_monthly_closing_prices(symbols)
        
        if monthly_data is not None and not monthly_data.empty:
            # Format the data for display
            formatted_data = fetcher.format_output_data(monthly_data, name)
            
            if formatted_data is not None:
                # Display summary
                print(f"\n✓ Data found for {name}")
                print(f"  Data points: {len(formatted_data)}")
                print(f"  Date range: {formatted_data['Date'].iloc[0]} to {formatted_data['Date'].iloc[-1]}")
                print(f"  Symbol used: {formatted_data['Symbol'].iloc[0]}")
                
                # Format data for JSON
                stock_json_data = fetcher.format_for_json(formatted_data, symbols)
                
                if stock_json_data:
                    # Add to combined JSON data
                    all_stocks_json_data.append(stock_json_data)
                    
                    # Save individual JSON
                    fetcher.save_individual_json(stock_json_data, timestamp)
                    
                    successful_stocks += 1
                else:
                    print(f"✗ Could not format JSON data for {name}")
                    failed_stocks += 1
            else:
                print(f"✗ Could not format data for {name}")
                failed_stocks += 1
        else:
            print(f"✗ No data found for {name}")
            failed_stocks += 1
    
    # Save all data combined to JSON
    if all_stocks_json_data:
        print(f"\n{'='*50}")
        print(f"Saving collated data for {successful_stocks} stock(s)...")
        
        # Save to JSON
        fetcher.save_to_json(all_stocks_json_data, json_filename)
        
        # Display summary
        print(f"\nSummary:")
        print(f"Total stocks processed: {len(stocks_list)}")
        print(f"Successfully fetched: {successful_stocks}")
        print(f"Failed to fetch: {failed_stocks}")
        print(f"Collated JSON saved to: {json_filename}")
        
        # Calculate total data points
        total_data_points = sum(stock['data_points'] for stock in all_stocks_json_data)
        print(f"Total monthly data points: {total_data_points}")
        
        # Show sample of data structure
        if all_stocks_json_data:
            print(f"\nSample data structure (first stock):")
            sample = {
                "name": all_stocks_json_data[0]["name"],
                "actual_symbol_used": all_stocks_json_data[0]["actual_symbol_used"],
                "data_points": all_stocks_json_data[0]["data_points"],
                "first_month": all_stocks_json_data[0]["monthly_prices"][0],
                "last_month": all_stocks_json_data[0]["monthly_prices"][-1]
            }
            print(json.dumps(sample, indent=2, ensure_ascii=False, default=str))
    else:
        print("\n✗ No data was fetched for any stock")

if __name__ == "__main__":
    main()