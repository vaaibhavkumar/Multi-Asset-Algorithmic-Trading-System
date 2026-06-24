import json
import os

def load_market_config(market_filename: str) -> dict:
    """Loads ticker and index array from a specified JSON configuration file securely using UTF-8."""
    base_path = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(base_path, "..", "config", market_filename)
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")
        
    # FIX: typo error from "g" to "r"
    with open(config_path, "r", encoding="utf-8") as file:
        config_data = json.load(file)
        
    return config_data