import requests
import pandas as pd
from datetime import datetime
import json

class IndianStockDataFetcher:
    def __init__(self):
        self.nse_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
    def get_nse_data(self, symbol="TARIL"):
        """Fetch data from NSE"""
        try:
            # NSE API endpoint
            url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
            
            # First get cookies
            session = requests.Session()
            session.get("https://www.nseindia.com", headers=self.nse_headers)
            
            # Then get data
            response = session.get(url, headers=self.nse_headers)
            
            if response.status_code == 200:
                data = response.json()
                return self.parse_nse_data(data)
            else:
                print(f"NSE API Error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error fetching NSE data: {e}")
            return None
    
    def parse_nse_data(self, data):
        """Parse NSE API response"""
        try:
            price_info = data.get('priceInfo', {})
            metadata = data.get('metadata', {})
            security_info = data.get('securityInfo', {})
            
            nse_data = {
                'Exchange': 'NSE',
                'Symbol': metadata.get('symbol', 'N/A'),
                'Company Name': metadata.get('companyName', 'N/A'),
                'Current Price': price_info.get('lastPrice', 'N/A'),
                'Change': price_info.get('change', 'N/A'),
                '% Change': price_info.get('pChange', 'N/A'),
                'Previous Close': price_info.get('previousClose', 'N/A'),
                'Open': price_info.get('open', 'N/A'),
                'Day High': price_info.get('intraDayHighLow', {}).get('max', 'N/A'),
                'Day Low': price_info.get('intraDayHighLow', {}).get('min', 'N/A'),
                '52 Week High': price_info.get('weekHighLow', {}).get('max', 'N/A'),
                '52 Week Low': price_info.get('weekHighLow', {}).get('min', 'N/A'),
                'Volume': price_info.get('totalTradedVolume', 'N/A'),
                'Market Cap (Cr)': 'N/A',  # Will need separate calculation
            }
            
            return nse_data
            
        except Exception as e:
            print(f"Error parsing NSE data: {e}")
            return None
    
    def get_bse_data(self, code="532928"):  # BSE code for Transformers and Rectifiers
        """Fetch data from BSE"""
        try:
            url = f"https://api.bseindia.com/BseIndiaAPI/api/StockReachGraph/w?scripcode={code}&flag=0"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.bseindia.com/',
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                return self.parse_bse_data(data, code)
            else:
                print(f"BSE API Error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error fetching BSE data: {e}")
            return None
    
    def parse_bse_data(self, data, code):
        """Parse BSE API response"""
        try:
            # BSE data structure varies, this is a basic parsing
            bse_data = {
                'Exchange': 'BSE',
                'BSE Code': code,
                'Current Price': data.get('CurrRate', 'N/A'),
                'Change': data.get('Change', 'N/A'),
                '% Change': data.get('ChangePercent', 'N/A'),
                'Previous Close': data.get('PrevClose', 'N/A'),
                'Open': data.get('OpenRate', 'N/A'),
                'Day High': data.get('HighRate', 'N/A'),
                'Day Low': data.get('LowRate', 'N/A'),
                'Volume': data.get('TotalTradedVol', 'N/A'),
            }
            
            return bse_data
            
        except Exception as e:
            print(f"Error parsing BSE data: {e}")
            return None
    
    def get_financial_ratios(self, symbol="TRANSFOR"):
        """Get financial ratios from Screener.in"""
        try:
            url = f"https://www.screener.in/api/company/{symbol}/"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                return self.parse_financial_data(data)
            else:
                print(f"Screener API Error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error fetching financial data: {e}")
            return None
    
    def parse_financial_data(self, data):
        """Parse financial data from Screener"""
        try:
            ratios = data.get('ratios', [{}])[0] if data.get('ratios') else {}
            
            financial_data = {
                'P/E Ratio': ratios.get('pe', 'N/A'),
                'P/B Ratio': ratios.get('pb', 'N/A'),
                'Debt to Equity': ratios.get('debt_to_equity', 'N/A'),
                'ROE %': ratios.get('roe', 'N/A'),
                'ROCE %': ratios.get('roce', 'N/A'),
                'EPS': ratios.get('eps', 'N/A'),
                'Dividend Yield %': ratios.get('dividend_yield', 'N/A'),
                'Face Value': data.get('face_value', 'N/A'),
                'Book Value': ratios.get('book_value', 'N/A'),
                'Industry PE': ratios.get('industry_pe', 'N/A'),
                'Market Cap (Cr)': data.get('market_cap', 'N/A'),
            }
            
            return financial_data
            
        except Exception as e:
            print(f"Error parsing financial data: {e}")
            return None
    
    def get_all_data(self):
        """Get complete stock data"""
        print("Fetching data for TRANSFORMERS AND RECTIFIERS (INDIA) LIMITED")
        print("="*80)
        
        # Get NSE Data
        print("\n1. NSE Data:")
        nse_data = self.get_nse_data("TRANSFOR")  # NSE symbol
        if nse_data:
            for key, value in nse_data.items():
                print(f"{key:20}: {value}")
        
        # Get BSE Data
        print("\n2. BSE Data:")
        bse_data = self.get_bse_data("532928")  # BSE code
        if bse_data:
            for key, value in bse_data.items():
                print(f"{key:20}: {value}")
        
        # Get Financial Ratios
        print("\n3. Financial Ratios & Fundamentals:")
        financial_data = self.get_financial_ratios("TRANSFOR")
        if financial_data:
            for key, value in financial_data.items():
                print(f"{key:20}: {value}")
        
        # Combine all data
        all_data = {}
        if nse_data:
            all_data.update(nse_data)
        if bse_data:
            all_data.update(bse_data)
        if financial_data:
            all_data.update(financial_data)
        
        # Additional calculated metrics
        all_data['Timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return all_data

# Usage
if __name__ == "__main__":
    fetcher = IndianStockDataFetcher()
    
    # Get all data
    complete_data = fetcher.get_all_data()
    
    # Save to CSV if needed
    if complete_data:
        df = pd.DataFrame([complete_data])
        df.to_csv('taril_stock_data.csv', index=False)
        print("\nData saved to 'taril_stock_data.csv'")