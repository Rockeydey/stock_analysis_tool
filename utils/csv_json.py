"""
Convert a CSV file with sectors, names, and symbols to a nested JSON file.
Updated on : 2026-06-01
"""


import csv
import json
import os
from collections import defaultdict

def csv_to_json_share_specs(csv_file_path, json_file_path):
    """
    Convert a CSV file with sectors, names, and symbols to a nested JSON file.
    
    Args:
        csv_file_path (str): Path to the input CSV file
        json_file_path (str): Path to the output JSON file
    """
    # Dictionary to store data grouped by sector
    sectors_data = defaultdict(list)
    
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as csv_file:
            # Read CSV file with comma delimiter (default)
            csv_reader = csv.DictReader(csv_file)  # No need to specify delimiter, comma is default
            
            for row in csv_reader:
                sector = row['sectors'].strip()
                name = row['name'].strip()
                symbol_nse = row['symbol_nse'].strip()
                symbol_bse = row['symbol_bse'].strip()
                
                # Create symbol list (only include non-empty symbols)
                symbols = []
                if symbol_nse:
                    symbols.append(symbol_nse)
                if symbol_bse:
                    symbols.append(symbol_bse)
                
                # Create entry for this company
                company_entry = {
                    "symbol": symbols,
                    "name": name
                }
                
                # Add to sector group
                sectors_data[sector].append(company_entry)
        
        # Convert defaultdict to regular dict
        result = dict(sectors_data)
        
        # Write to JSON file
        with open(json_file_path, 'w', encoding='utf-8') as json_file:
            json.dump(result, json_file, indent=4, ensure_ascii=False)
        
        print(f"Successfully converted {csv_file_path} to {json_file_path}")
        return result
        
    except FileNotFoundError:
        print(f"Error: CSV file not found at {csv_file_path}")
        return None
    except Exception as e:
        print(f"Error processing CSV file: {e}")
        return None

# Example usage
if __name__ == "__main__":
    from utils.load_config import load_config
    config = load_config("config/local_config.json")
    csv_file_path = config.get("input_data_path", {}).get("all_stocks_data_path")
    json_file_path = config.get("output_path", {}).get("json_output_stock_spec")
    csv_to_json_share_specs(csv_file_path, json_file_path)
