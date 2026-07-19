import json
import os
import re
import time
import requests
from bs4 import BeautifulSoup
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CACHE_FILE = BASE_DIR.parent / "macro_cache.json"

def _get_cached_macro(key: str):
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE, "r") as file:
            return json.load(file).get(key)
    except (json.JSONDecodeError, IOError):
        return None

def _set_cached_macro(key: str, value: float) -> None:
    cache = {}
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as file:
                cache = json.load(file)
        except (json.JSONDecodeError, IOError):
            pass 
    cache[key] = value
    with open(CACHE_FILE, "w") as file:
        json.dump(cache, file, indent=4)

def _fetch_live_cpi_inflation() -> float:
    url = "https://tradingeconomics.com/pakistan/inflation-cpi"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() 
        soup = BeautifulSoup(response.text, "html.parser")
        match = re.search(r'Inflation Rate YoY\s*(\d+\.\d+)', soup.get_text(), re.IGNORECASE)
        return float(match.group(1)) if match else 0.0 
    except Exception as e:
        print(f"Error fetching live CPI: {e}")
        return 0.0

def check_inflation_rate() -> dict:
    """
    Core logic: Gets the current inflation rate using a cache-first approach.
    """
    key = "pk_cpi_yoy_inflation"
    cached_value = _get_cached_macro(key)
    
    # Not in cache: fetch live and save
    if cached_value is None:
        live_value = _fetch_live_cpi_inflation()
        _set_cached_macro(key, live_value)
        return {"inflation_rate": live_value, "source": "live", "is_stale": False}
        
    # In cache: check staleness (> 24 hours old)
    is_stale = False
    if os.path.exists(CACHE_FILE):
        if (time.time() - os.path.getmtime(CACHE_FILE)) > 86400:
            is_stale = True
            
    return {"inflation_rate": cached_value, "source": "cache", "is_stale": is_stale}

def override_inflation_rate(manual_rate: float) -> dict:
    """
    Core logic: Manually overrides the inflation rate stored in the cache.
    """
    key = "pk_cpi_yoy_inflation"
    
    _set_cached_macro(key, manual_rate)
    
    return {
        "status": "success",
        "updated_rate": manual_rate,
        "source": "manual_override"
    }

def real_return(nominal_rate: float, inflation_rate: float = None) -> dict:
    """
    Core logic: Calculates the real rate of return using the Fisher equation.
    Automatically grabs the latest inflation rate from the cache/live if not provided.
    """
    source = "user_provided"
    
    if inflation_rate is None:
        inflation_data = check_inflation_rate()
        inflation_rate = inflation_data["inflation_rate"]
        source = f"auto_fetched ({inflation_data['source']})"
        
    nominal_decimal = nominal_rate / 100
    inflation_decimal = inflation_rate / 100
    
    if inflation_decimal <= -1:
        raise ValueError("Inflation rate cannot be -100% or less.")
        
    real_decimal = ((1 + nominal_decimal) / (1 + inflation_decimal)) - 1
    real_percentage = real_decimal * 100
    
    approx_percentage = nominal_rate - inflation_rate
    
    return {
        "nominal_rate": nominal_rate,
        "inflation_rate": inflation_rate,
        "real_rate_exact": real_percentage,
        "real_rate_approximate": approx_percentage,
        "inflation_source": source
    }

def future_cost(current_cost: float, years: float, inflation_rate: float = None) -> dict:
    """
    Core logic: Projects the future cost of an expense adjusted for inflation.
    Automatically grabs the latest inflation rate from the cache/live if not provided.
    """
    source = "user_provided"
    
    if inflation_rate is None:
        inflation_data = check_inflation_rate()
        inflation_rate = inflation_data["inflation_rate"]
        source = f"auto_fetched ({inflation_data['source']})"
        
    inflation_decimal = inflation_rate / 100
    
    projected_cost = current_cost * ((1 + inflation_decimal) ** years)
    
    return {
        "current_cost": current_cost,
        "projected_cost": projected_cost,
        "years": years,
        "inflation_rate": inflation_rate,
        "inflation_source": source
    }