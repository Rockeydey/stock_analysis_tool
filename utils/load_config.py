"""

Updated on : 2026-06-11
"""


import json

def load_config(config_file_path):
    """
    Load configuration settings from a JSON file and filter by required=True.

    Args:
        config_file_path (str): The path to the configuration JSON file.
    Returns:
        dict: A dictionary containing only the inputs from required sections.
    """
    try:
        with open(config_file_path, 'r') as file:
            config = json.load(file)
        
        # Filter: keep only sections where required is "True" and extract their inputs
        filtered_config = {}
        for key, value in config.items():
            if isinstance(value, dict) and value.get("required") == "True":
                if "inputs" in value:
                    filtered_config[key] = value["inputs"]
        
        return filtered_config if filtered_config else None
        
    except FileNotFoundError:
        print(f"Configuration file not found: {config_file_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON from the configuration file: {config_file_path}")
        return None

if __name__ == "__main__":
    config = load_config("config/local_config.json")
    if config:
        print("Configuration loaded successfully:")
        print(config)
    else:
        print("Failed to load configuration.")