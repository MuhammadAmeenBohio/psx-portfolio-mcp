import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "portfolio_manager.db")

def get_db_connection():
    """
    Creates and returns a connection to the SQLite database.
    Sets row_factory so we can access columns by name.
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initializes the clean SQLite database for the Analysis Engine.
    Creates only the necessary tables for simulations.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Table 1: Official Ticker Mapping 
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ticker_mapping (
                ticker TEXT PRIMARY KEY,
                company_name TEXT NOT NULL
            )
        ''')
        
        # Table 2: Corporate Actions 
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS corporate_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                action_type TEXT NOT NULL,
                amount_or_ratio REAL NOT NULL,
                ex_date TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        print(f"Clean Analysis Database initialized at {DB_FILE}")

init_db()