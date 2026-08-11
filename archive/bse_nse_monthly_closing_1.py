import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf
import json
import os

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
        
        return output_df
    
    def save_to_csv(self, data, filename="monthly_closing_prices.csv"):
        """Save monthly closing prices to CSV file"""
        if data is None or data.empty:
            print("No data to save")
            return
        
        # Ensure output directory exists
        os.makedirs('output', exist_ok=True)
        
        # Append if file exists, otherwise create new
        file_exists = os.path.exists(filename)
        
        if file_exists:
            data.to_csv(filename, mode='a', header=False, index=False)
            print(f"✓ Data appended to {filename}")
        else:
            data.to_csv(filename, index=False)
            print(f"✓ Data saved to {filename}")
    
    def save_to_excel(self, data, filename="monthly_closing_prices.xlsx"):
        """Save monthly closing prices to Excel file"""
        if data is None or data.empty:
            print("No data to save")
            return
        
        # Ensure output directory exists
        os.makedirs('output', exist_ok=True)
        
        # Create Excel writer
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            data.to_excel(writer, sheet_name='Monthly_Prices', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Monthly_Prices']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        print(f"✓ Data saved to {filename}")

def main():
    """Main function to fetch monthly closing prices for all stocks in JSON"""
    print("FETCHING MONTHLY CLOSING PRICES - LAST 10 YEARS")
    print("="*60)
    
    fetcher = StockMonthlyDataFetcher()
    
    # Read stocks list from JSON file
    input_path = os.path.join('input', 'stocks_list.json')
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            stocks_json = json.load(f)
            stocks_list = stocks_json.get('stocks', [])
    except Exception as e:
        print(f"Error reading {input_path}: {e}")
        print("Please create input/stocks_list.json with your stock list")
        return
    
    if not stocks_list:
        print(f"No stocks found in {input_path}")
        return
    
    # Create output directory
    os.makedirs('output', exist_ok=True)
    
    # Define output filenames
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_filename = f"output/monthly_closing_prices_{timestamp}.csv"
    excel_filename = f"output/monthly_closing_prices_{timestamp}.xlsx"
    
    all_data_frames = []  # To store all data for combined output
    
    print(f"\nProcessing {len(stocks_list)} stock(s)...")
    
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
            # Format the data
            formatted_data = fetcher.format_output_data(monthly_data, name)
            
            if formatted_data is not None:
                # Display first few rows
                print(f"\nFirst few rows for {name}:")
                print(formatted_data.head())
                print(f"\nData points: {len(formatted_data)}")
                print(f"Date range: {formatted_data['Date'].iloc[0]} to {formatted_data['Date'].iloc[-1]}")
                
                # Save individual stock data
                stock_csv = f"output/{name.replace(' ', '_')}_{timestamp}.csv"
                formatted_data.to_csv(stock_csv, index=False)
                print(f"✓ Individual data saved to {stock_csv}")
                
                # Add to combined data
                all_data_frames.append(formatted_data)
            else:
                print(f"✗ Could not format data for {name}")
        else:
            print(f"✗ No data found for {name}")
    
    # Save all data combined
    if all_data_frames:
        # Combine all DataFrames
        combined_data = pd.concat(all_data_frames, ignore_index=True)
        
        # Sort by stock name and date
        combined_data = combined_data.sort_values(['Stock_Name', 'Date'])
        
        # Save to combined files
        print(f"\n{'='*50}")
        print(f"Saving combined data for {len(all_data_frames)} stock(s)...")
        
        # Save to CSV
        combined_data.to_csv(csv_filename, index=False)
        print(f"✓ Combined CSV saved to {csv_filename}")
        
        # Save to Excel
        fetcher.save_to_excel(combined_data, excel_filename)
        
        # Display summary
        print(f"\nSummary:")
        print(f"Total records: {len(combined_data)}")
        print(f"Unique stocks: {combined_data['Stock_Name'].nunique()}")
        print(f"Date range: {combined_data['Date'].min()} to {combined_data['Date'].max()}")
    else:
        print("\n✗ No data was fetched for any stock")

if __name__ == "__main__":
    main()