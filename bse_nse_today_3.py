import requests
import pandas as pd
from datetime import datetime
import yfinance as yf
import time
import json
import openpyxl
import os

class IndianStockDataFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.nseindia.com/',
            'Origin': 'https://www.nseindia.com',
        }
        
    def get_nse_data_alternative(self, symbol="TRANSFOR"):
        """Alternative method for NSE data"""
        try:
            # Method 1: Using NSE's official API with cookies
            base_url = "https://www.nseindia.com"
            quote_url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
            
            # First get cookies
            self.session.get(base_url, headers=self.headers, timeout=10)
            time.sleep(2)
            
            # Get quote data
            response = self.session.get(quote_url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self.parse_nse_alternative(data, symbol)
            else:
                # Try alternative endpoint
                return self.get_nse_data_fallback(symbol)
                
        except Exception as e:
            print(f"Error in NSE alternative method: {e}")
            return self.get_nse_data_fallback(symbol)
    
    def parse_nse_alternative(self, data, symbol):
        """Parse NSE API response"""
        try:
            info = data.get('info', {})
            metadata = data.get('metadata', {})
            price_info = data.get('priceInfo', {})
            
            nse_data = {
                'Exchange': 'NSE',
                'Symbol': symbol,
                'Company Name': metadata.get('companyName', info.get('companyName', 'N/A')),
                'Current Price': price_info.get('lastPrice', 'N/A'),
                'Change': price_info.get('change', 'N/A'),
                '% Change': f"{price_info.get('pChange', 'N/A')}%",
                'Previous Close': price_info.get('previousClose', 'N/A'),
                'Open': price_info.get('open', 'N/A'),
                'Day High': price_info.get('intraDayHighLow', {}).get('max', 'N/A'),
                'Day Low': price_info.get('intraDayHighLow', {}).get('min', 'N/A'),
                '52 Week High': price_info.get('weekHighLow', {}).get('max', 'N/A'),
                '52 Week Low': price_info.get('weekHighLow', {}).get('min', 'N/A'),
                'Volume': self.format_number(price_info.get('totalTradedVolume', 0)),
                'Avg Volume': self.format_number(info.get('averageTradedVolume', 0)),
            }
            
            return nse_data
            
        except Exception as e:
            print(f"Error parsing NSE data: {e}")
            return None
    
    def get_nse_data_fallback(self, symbol="TRANSFOR"):
        """Fallback method using web scraping"""
        try:
            url = f"https://www1.nseindia.com/live_market/dynaContent/live_watch/get_quote/GetQuote.jsp?symbol={symbol}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Parse HTML response
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract data from HTML (structure may change)
                nse_data = {
                    'Exchange': 'NSE',
                    'Symbol': symbol,
                    'Source': 'Web Scraping',
                }
                
                # Look for specific divs or spans containing data
                price_div = soup.find('div', {'id': 'responseDiv'})
                if price_div:
                    text = price_div.get_text()
                    # Parse JSON if available
                    if '{' in text and '}' in text:
                        import json
                        start = text.find('{')
                        end = text.rfind('}') + 1
                        json_str = text[start:end]
                        data = json.loads(json_str)
                        if 'data' in data and len(data['data']) > 0:
                            stock_data = data['data'][0]
                            nse_data.update({
                                'Company Name': stock_data.get('companyName', 'N/A'),
                                'Current Price': stock_data.get('lastPrice', 'N/A'),
                                '% Change': stock_data.get('pChange', 'N/A'),
                                'Previous Close': stock_data.get('previousClose', 'N/A'),
                            })
                
                return nse_data
                
        except Exception as e:
            print(f"Error in NSE fallback: {e}")
            return None
    
    def get_bse_data_alternative(self, scrip_code="532928"):
        """Alternative method for BSE data"""
        try:
            # Method 1: Using BSE's new API
            url = f"https://api.bseindia.com/BseIndiaAPI/api/StockTrading/w?scripcode={scrip_code}&DebtFlag=&series=EQ"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.bseindia.com/',
                'Host': 'api.bseindia.com',
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200 and response.text.strip():
                try:
                    data = response.json()
                    return self.parse_bse_alternative(data, scrip_code)
                except json.JSONDecodeError:
                    # Try parsing as text
                    return self.parse_bse_text(response.text, scrip_code)
            else:
                return self.get_bse_data_fallback(scrip_code)
                
        except Exception as e:
            print(f"Error in BSE alternative: {e}")
            return self.get_bse_data_fallback(scrip_code)
    
    def parse_bse_alternative(self, data, scrip_code):
        """Parse BSE API response"""
        try:
            bse_data = {
                'Exchange': 'BSE',
                'BSE Code': scrip_code,
                'Current Price': data.get('CurrRate', data.get('LTP', 'N/A')),
                'Change': data.get('Change', data.get('Chg', 'N/A')),
                '% Change': f"{data.get('ChangePercent', data.get('ChgPer', 'N/A'))}%",
                'Previous Close': data.get('PrevClose', 'N/A'),
                'Open': data.get('OpenRate', data.get('Open', 'N/A')),
                'Day High': data.get('HighRate', data.get('High', 'N/A')),
                'Day Low': data.get('LowRate', data.get('Low', 'N/A')),
                'Volume': self.format_number(data.get('TotalTradedVol', data.get('Volume', 0))),
            }
            
            return bse_data
            
        except Exception as e:
            print(f"Error parsing BSE data: {e}")
            return None
    
    def parse_bse_text(self, text, scrip_code):
        """Parse BSE text response"""
        try:
            # Parse CSV-like response
            lines = text.strip().split('\n')
            if len(lines) > 1:
                values = lines[1].split(',')
                if len(values) >= 10:
                    bse_data = {
                        'Exchange': 'BSE',
                        'BSE Code': scrip_code,
                        'Current Price': values[4],
                        'Change': values[5],
                        '% Change': f"{values[6]}%",
                        'Previous Close': values[7],
                        'Open': values[1],
                        'Day High': values[2],
                        'Day Low': values[3],
                        'Volume': self.format_number(values[8]),
                    }
                    return bse_data
            return None
        except:
            return None
    
    def get_bse_data_fallback(self, scrip_code):
        """Fallback for BSE using web scraping"""
        try:
            url = f"https://www.bseindia.com/stock-share-price/{scrip_code}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')
                
                bse_data = {
                    'Exchange': 'BSE',
                    'BSE Code': scrip_code,
                    'Source': 'Web Scraping',
                }
                
                # Try to find price element (BSE website structure)
                price_span = soup.find('span', {'id': 'idcr'})
                if price_span:
                    bse_data['Current Price'] = price_span.text.strip()
                
                change_span = soup.find('span', {'id': 'idch'})
                if change_span:
                    change_text = change_span.text.strip()
                    bse_data['Change'] = change_text
                    if '(' in change_text and ')' in change_text:
                        pct = change_text[change_text.find('(')+1:change_text.find(')')]
                        bse_data['% Change'] = pct
                
                return bse_data
                
        except Exception as e:
            print(f"Error in BSE fallback: {e}")
            return None
    
    def get_financial_data(self, company_name="transformers-and-rectifiers"):
        """Get financial data from alternative sources"""
        try:
            # Method 1: Using Moneycontrol
            mc_data = self.get_moneycontrol_data(company_name)
            if mc_data:
                return mc_data
            
            # Method 2: Using Investing.com alternative
            return self.get_investing_data()
            
        except Exception as e:
            print(f"Error getting financial data: {e}")
            return None
    
    def get_moneycontrol_data(self, company_name):
        """Get data from Moneycontrol"""
        try:
            url = f"https://www.moneycontrol.com/india/stockpricequote/transformers/transformersrectifiersindia/{company_name}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')
                
                financial_data = {
                    'Source': 'Moneycontrol',
                }
                
                # Extract key ratios (Moneycontrol specific selectors)
                # Note: These selectors might change
                pe_span = soup.find('div', {'id': 'pe_ratio'})
                if pe_span:
                    financial_data['P/E Ratio'] = pe_span.text.strip()
                
                # Look for other ratios
                for div in soup.find_all('div', {'class': 'value_txtfr'}):
                    text = div.text.strip()
                    if 'P/E' in text:
                        financial_data['P/E Ratio'] = text.split(':')[-1].strip()
                    elif 'Industry P/E' in text:
                        financial_data['Industry P/E'] = text.split(':')[-1].strip()
                
                return financial_data
                
        except Exception as e:
            print(f"Moneycontrol error: {e}")
            return None
    
    def get_investing_data(self):
        """Get data from Investing.com alternative"""
        try:
            # Using yfinance for fundamental data
            stock = yf.Ticker("TARIL.NS")
            info = stock.info
            
            financial_data = {
                'Source': 'Yahoo Finance',
                'P/E Ratio': info.get('trailingPE', 'N/A'),
                'Forward P/E': info.get('forwardPE', 'N/A'),
                'PEG Ratio': info.get('pegRatio', 'N/A'),
                'P/B Ratio': info.get('priceToBook', 'N/A'),
                'Beta': info.get('beta', 'N/A'),
                'Market Cap': self.format_market_cap(info.get('marketCap', 0)),
                'Shares Outstanding': self.format_number(info.get('sharesOutstanding', 0)),
                'EPS': info.get('trailingEps', 'N/A'),
                'ROE': f"{info.get('returnOnEquity', 'N/A')}%" if info.get('returnOnEquity') else 'N/A',
                'ROA': f"{info.get('returnOnAssets', 'N/A')}%" if info.get('returnOnAssets') else 'N/A',
                'Debt to Equity': info.get('debtToEquity', 'N/A'),
                'Dividend Yield': f"{info.get('dividendYield', 'N/A')}%" if info.get('dividendYield') else 'N/A',
                'Industry': info.get('industry', 'N/A'),
                'Sector': info.get('sector', 'N/A'),
            }
            
            return financial_data
            
        except Exception as e:
            print(f"Yahoo Finance error: {e}")
            return None
    
    def get_all_data_yfinance(self, symbols=None):
        """Get all data using yfinance (most reliable)

        symbols: optional list of ticker strings to try in order. If None,
        a default set will be used.
        """
        try:
            # Try provided symbols or fall back to defaults
            symbols = symbols or ["TARIL.NS", "TRANSFOR.NS", "532928.BO"]

            for symbol in symbols:
                try:
                    print(f"Trying symbol: {symbol}")
                    stock = yf.Ticker(symbol)
                    info = stock.info
                    
                    if info and info.get('regularMarketPrice'):
                        print(f"✓ Found data for {symbol}")
                        
                        # Get historical data for % change
                        hist = stock.history(period="2d")
                        
                        if not hist.empty and len(hist) >= 2:
                            prev_close = hist['Close'].iloc[-2]
                            current_price = hist['Close'].iloc[-1]
                            pct_change = ((current_price - prev_close) / prev_close) * 100
                        else:
                            prev_close = info.get('previousClose', 'N/A')
                            current_price = info.get('regularMarketPrice', 'N/A')
                            pct_change = info.get('regularMarketChangePercent', 'N/A')
                        
                        # Get additional data
                        try:
                            financials = stock.financials
                            balance_sheet = stock.balance_sheet
                            cashflow = stock.cashflow
                        except:
                            financials = balance_sheet = cashflow = None
                        
                        all_data = {
                            'Symbol': symbol,
                            'Company Name': info.get('longName', 'TRANSFORMERS AND RECTIFIERS (INDIA) LIMITED'),
                            'Current Price': current_price,
                            'Previous Close': prev_close,
                            '% Change': f"{pct_change:.2f}%" if isinstance(pct_change, (int, float)) else pct_change,
                            'Day High': info.get('dayHigh', 'N/A'),
                            'Day Low': info.get('dayLow', 'N/A'),
                            '52 Week High': info.get('fiftyTwoWeekHigh', 'N/A'),
                            '52 Week Low': info.get('fiftyTwoWeekLow', 'N/A'),
                            'Volume': self.format_number(info.get('volume', 0)),
                            'Avg Volume': self.format_number(info.get('averageVolume', 0)),
                            'Market Cap': self.format_market_cap(info.get('marketCap', 0)),
                            'P/E Ratio': info.get('trailingPE', 'N/A'),
                            'Forward P/E': info.get('forwardPE', 'N/A'),
                            'PEG Ratio': info.get('pegRatio', 'N/A'),
                            'P/B Ratio': info.get('priceToBook', 'N/A'),
                            'Beta': info.get('beta', 'N/A'),
                            'Shares Outstanding': self.format_number(info.get('sharesOutstanding', 0)),
                            'Float Shares': self.format_number(info.get('floatShares', 0)),
                            'Short Ratio': info.get('shortRatio', 'N/A'),
                            'Book Value': info.get('bookValue', 'N/A'),
                            'EPS': info.get('trailingEps', 'N/A'),
                            'Revenue Growth': f"{info.get('revenueGrowth', 'N/A')}%" if info.get('revenueGrowth') else 'N/A',
                            'Earnings Growth': f"{info.get('earningsGrowth', 'N/A')}%" if info.get('earningsGrowth') else 'N/A',
                            'ROE': f"{info.get('returnOnEquity', 'N/A')}%" if info.get('returnOnEquity') else 'N/A',
                            'ROA': f"{info.get('returnOnAssets', 'N/A')}%" if info.get('returnOnAssets') else 'N/A',
                            'Operating Margin': f"{info.get('operatingMargins', 'N/A')}%" if info.get('operatingMargins') else 'N/A',
                            'Profit Margin': f"{info.get('profitMargins', 'N/A')}%" if info.get('profitMargins') else 'N/A',
                            'Debt to Equity': info.get('debtToEquity', 'N/A'),
                            'Current Ratio': info.get('currentRatio', 'N/A'),
                            'Quick Ratio': info.get('quickRatio', 'N/A'),
                            'Dividend Yield': f"{info.get('dividendYield', 'N/A')}%" if info.get('dividendYield') else 'N/A',
                            'Dividend Rate': info.get('dividendRate', 'N/A'),
                            'Payout Ratio': f"{info.get('payoutRatio', 'N/A')}%" if info.get('payoutRatio') else 'N/A',
                            'Industry': info.get('industry', 'Electrical Equipment'),
                            'Sector': info.get('sector', 'Industrials'),
                            'Website': info.get('website', 'N/A'),
                            'Country': info.get('country', 'India'),
                            'Exchange': info.get('exchange', symbol.split('.')[-1]),
                            'Currency': info.get('currency', 'INR'),
                            'Data Source': 'Yahoo Finance',
                            'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        }
                        
                        return all_data
                        
                except Exception as e:
                    print(f"  Error with {symbol}: {e}")
                    continue
            
            print("✗ Could not fetch data using yfinance")
            return None
            
        except Exception as e:
            print(f"Error in yfinance method: {e}")
            return None
    
    def format_number(self, num):
        """Format large numbers with K, M, B suffixes"""
        if isinstance(num, (int, float)):
            if num >= 1_000_000_000:
                return f"{num/1_000_000_000:.2f}B"
            elif num >= 1_000_000:
                return f"{num/1_000_000:.2f}M"
            elif num >= 1_000:
                return f"{num/1_000:.2f}K"
            else:
                return str(num)
        return num
    
    def format_market_cap(self, market_cap):
        """Format market capitalization"""
        if isinstance(market_cap, (int, float)):
            if market_cap >= 1_000_000_000_000:
                return f"₹{market_cap/1_000_000_000_000:.2f}T"
            elif market_cap >= 1_000_000_000:
                return f"₹{market_cap/1_000_000_000:.2f}B"
            elif market_cap >= 1_000_000:
                return f"₹{market_cap/1_000_000:.2f}M"
            else:
                return f"₹{market_cap:,.0f}"
        return market_cap
    
    def display_data(self, data):
        """Display data in formatted table"""
        if not data:
            print("No data to display")
            return
        
        print("\n" + "="*80)
        print("TRANSFORMERS AND RECTIFIERS (INDIA) LIMITED - COMPLETE STOCK DATA")
        print("="*80)
        
        # Group data by category
        categories = {
            'Price Information': [],
            'Volume & Market Data': [],
            'Valuation Ratios': [],
            'Financial Ratios': [],
            'Company Information': [],
        }
        
        for key, value in data.items():
            if any(x in key.lower() for x in ['price', 'change', 'high', 'low', 'close']):
                categories['Price Information'].append((key, value))
            elif any(x in key.lower() for x in ['volume', 'market cap', 'shares']):
                categories['Volume & Market Data'].append((key, value))
            elif any(x in key.lower() for x in ['pe', 'pb', 'peg', 'beta']):
                categories['Valuation Ratios'].append((key, value))
            elif any(x in key.lower() for x in ['ro', 'margin', 'ratio', 'eps', 'debt', 'dividend']):
                categories['Financial Ratios'].append((key, value))
            else:
                categories['Company Information'].append((key, value))
        
        # Display each category
        for category, items in categories.items():
            if items:
                print(f"\n{category}:")
                print("-" * 50)
                for key, value in items:
                    print(f"{key:30}: {value}")
        
        print("\n" + "="*80)
    
    def save_to_csv(self, data, filename="taril_stock_data.csv"):
        """Save data to CSV file"""
        if data:
            # Ensure directory exists
            dirpath = os.path.dirname(filename)
            if dirpath:
                os.makedirs(dirpath, exist_ok=True)

            df = pd.DataFrame([data])

            # Append if file exists, otherwise write header
            if os.path.exists(filename):
                df.to_csv(filename, mode='a', header=False, index=False)
            else:
                df.to_csv(filename, index=False)

            print(f"\n✓ Data saved to {filename}")
    
    def save_to_excel(self, data, filename="taril_stock_data.xlsx"):
        """Save data to Excel with formatting"""
        if data:
            df = pd.DataFrame([data])
            
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Stock Data', index=False)
                
                # Get workbook and worksheet for formatting
                workbook = writer.book
                worksheet = writer.sheets['Stock Data']
                
                # Adjust column width
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
                
                # Add header formatting
                header_fill = openpyxl.styles.PatternFill(start_color="366092", 
                                                         end_color="366092", 
                                                         fill_type="solid")
                header_font = openpyxl.styles.Font(color="FFFFFF", bold=True)
                
                for cell in worksheet[1]:
                    cell.fill = header_fill
                    cell.font = header_font
            
            print(f"✓ Data saved to {filename}")

def main():
    """Main function"""
    print("Fetching data for TRANSFORMERS AND RECTIFIERS (INDIA) LIMITED")
    print("="*80)
    
    fetcher = IndianStockDataFetcher()
    # Read the stocks list and fetch only those entries
    input_path = os.path.join('input', 'stocks_list.json')
    output_file = os.path.join('output', 'all_stocks_data.csv')

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            stocks_json = json.load(f)
            stocks_list = stocks_json.get('stocks', [])
    except Exception as e:
        print(f"Error reading {input_path}: {e}")
        print("Falling back to single-symbol fetch (default).")
        data = fetcher.get_all_data_yfinance()
        if data:
            fetcher.display_data(data)
            fetcher.save_to_csv(data, filename=output_file)
        return

    if not stocks_list:
        print(f"No stocks found in {input_path}")
        return

    for stock in stocks_list:
        name = stock.get('name', 'Unknown')
        symbols = stock.get('symbol', [])
        if isinstance(symbols, str):
            symbols = [symbols]

        print(f"\nFetching: {name}")
        print(f"Trying symbols: {symbols}")

        data = fetcher.get_all_data_yfinance(symbols=symbols)

        if data:
            # Add metadata about the requested input
            data['Requested Name'] = name
            data['Requested Symbols'] = ','.join(symbols)
            fetcher.display_data(data)
            fetcher.save_to_csv(data, filename=output_file)
        else:
            print(f"No data found for {name} (symbols: {symbols})")

if __name__ == "__main__":
    main()