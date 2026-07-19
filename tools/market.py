import psxdata
import sqlite3
import math
import pandas as pd
from db_setup.portfolio_manager_setup import get_db_connection

def _seed_official_tickers() -> bool:
    """
    Internal helper to seed the database using psxdata.
    Returns True if successful, False otherwise.
    """
    try:
        data_dict = psxdata.eligible_scrips()
        df = data_dict.get('table_0')
        
        if df is None or df.empty:
            return False
            
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM ticker_mapping')
            
            for _, row in df.iterrows():
                symbol = str(row['symbol']).strip().upper()
                name = str(row['name']).strip()
                
                if symbol and name and "RIGHT" not in name.upper() and "-" not in symbol:
                    cursor.execute('''
                        INSERT OR REPLACE INTO ticker_mapping (ticker, company_name)
                        VALUES (?, ?)
                    ''', (symbol, name))
            conn.commit()
        return True
    except Exception as e:
        print(f"Failed to auto-seed tickers: {e}")
        return False

def _search_ticker(query: str) -> dict:
    """
    Searches the local database for a ticker or company name.
    Automatically handles cold starts if the database is empty.
    """
    try:
        with get_db_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) as count FROM ticker_mapping')
            row_count = cursor.fetchone()['count']
            
            if row_count == 0:
                print("Cold start detected! Auto-seeding database with official PSX tickers...")
                success = _seed_official_tickers()
                if not success:
                    return {
                        "status": "error", 
                        "message": "Database is empty and auto-seeding failed."
                    }
            
            cursor.execute('''
                SELECT ticker, company_name FROM ticker_mapping 
                WHERE ticker LIKE ? OR company_name LIKE ?
                LIMIT 5
            ''', (f"%{query.upper()}%", f"%{query}%"))
            
            matches = [dict(row) for row in cursor.fetchall()]
            
            if not matches:
                return {"status": "not_found", "query": query, "message": "No matches found."}
                
            return {
                "status": "success",
                "query": query,
                "matches": matches
            }
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

def _fetch_stock_quote(ticker: str) -> dict:
    """
    Core logic: Fetches real-time market data for a given stock 
    using the psxdata library and safely normalizes the nested structure.
    """
    ticker = ticker.upper()
    
    try:
        # Fetch the live data
        quote_data = psxdata.quote(ticker)
        
        # Convert Pandas object to dictionary safely
        if hasattr(quote_data, "to_dict"):
            raw_dict = quote_data.to_dict()
        else:
            raw_dict = dict(quote_data)
            
        # Helper function to unpack nested {"0": value} safely and clean up NaN values
        def unpack_val(key, default="N/A"):
            nested_dict = raw_dict.get(key, {})
            if isinstance(nested_dict, dict) and "0" in nested_dict:
                val = nested_dict["0"]
                # Check for float NaN values
                if isinstance(val, float) and math.isnan(val):
                    return default
                return val
            return default

        # Safely extract and format the required screener fields
        price = unpack_val("price")
        pe_ratio = unpack_val("pe_ratio")
        div_yield = unpack_val("dividend_yield")
        market_cap = unpack_val("market_cap")
        change_pct = unpack_val("change_pct")
        
        return {
            "status": "success",
            "ticker": ticker,
            "price": price,
            "pe_ratio": pe_ratio,
            "dividend_yield_percent": div_yield,
            "market_cap": market_cap,
            "day_change": change_pct,
            "currency": "PKR"
        }
        
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Failed to fetch quote for {ticker}: {str(e)}"
        }
    
def _get_historical_prices(query: str, start_date: str, end_date: str) -> dict:
    """
    Fetches historical OHLCV data from the PSX, ensuring strict 
    chronological sorting and clean JSON-compatible formatting.
    """
    search_result = _search_ticker(query)
    
    if search_result.get("status") != "success" or not search_result.get("matches"):
        return {"error": f"Could not find an official ticker for '{query}'."}
        
    ticker = search_result["matches"][0]["ticker"]
        
    try:
        # 4. Fetch the data from psxdata
        df = psxdata.stocks(ticker, start=start_date, end=end_date)
        
        if df is None or df.empty:
            return {"error": f"No market data found for {ticker} between {start_date} and {end_date}."}
            
        date_col = 'date' if 'date' in df.columns else 'Date'
        
        df[date_col] = pd.to_datetime(df[date_col])
        
        df = df.sort_values(by=date_col, ascending=True)
        
        df[date_col] = df[date_col].dt.strftime('%Y-%m-%d')
        
        if 'index' in df.columns:
            df = df.drop(columns=['index'])
            
        return {
            "ticker": ticker, 
            "company_name": search_result["matches"][0]["company_name"],
            "data_points": len(df),
            "history": df.to_dict(orient="records")
        }
        
    except Exception as e:
        return {"error": f"Failed to fetch historical data from psxdata: {str(e)}"}
    
def _list_tickers() -> dict:
    """
    Retrieves the complete master list of all official PSX tickers from the database.
    Includes cold-start protection to rebuild the list if the database is empty.
    """
    try:
        with get_db_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) as count FROM ticker_mapping')
            row_count = cursor.fetchone()['count']
            
            if row_count == 0:
                print("Cold start detected! Auto-seeding database with official PSX tickers...")
                success = _seed_official_tickers()
                if not success:
                    return {
                        "status": "error", 
                        "message": "Database is empty and auto-seeding failed. Please check your internet connection."
                    }
            
            cursor.execute('''
                SELECT ticker, company_name 
                FROM ticker_mapping 
                ORDER BY ticker ASC
            ''')
            
            all_tickers = [dict(row) for row in cursor.fetchall()]
            
            return {
                "status": "success",
                "total_count": len(all_tickers),
                "tickers": all_tickers
            }
            
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Failed to list tickers: {str(e)}"
        }
    
def _get_index_constituents(index_name: str) -> dict:
    """
    Fetches the list of companies that make up a specific PSX index.
    Standardizes the index name string to ensure psxdata can read it.
    """
    try:
        clean_index = str(index_name).upper().replace(" ", "").replace("-", "")
        
        # Fetch the dataframe from the library
        df = psxdata.indices(clean_index)
        
        if df is None or df.empty:
            return {
                "status": "error", 
                "message": f"No data found for index '{index_name}'. Ensure it's a valid PSX index (e.g., KSE100, KMI30)."
            }
            
        df = df.reset_index()
        
        if 'index' in df.columns:
            df = df.drop(columns=['index'])
            
        return {
            "status": "success",
            "index_name": clean_index,
            "total_constituents": len(df),
            "constituents": df.to_dict(orient="records")
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to fetch index constituents for '{index_name}': {str(e)}"
        }
    
def _get_sector_summary() -> dict:
    """
    Fetches the aggregate performance of all market sectors on the PSX.
    """
    try:
        df = psxdata.sectors()
        
        if df is None or df.empty:
            return {
                "status": "error",
                "message": "No sector data found. The PSX might be undergoing maintenance or the market is closed."
            }
            
        df = df.reset_index()
        
        if 'index' in df.columns and len(df.columns) > 1:
            df = df.drop(columns=['index'])
            
        df = df.where(pd.notnull(df), None)
            
        return {
            "status": "success",
            "total_sectors": len(df),
            "sectors": df.to_dict(orient="records")
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to fetch sector summary from psxdata: {str(e)}"
        }