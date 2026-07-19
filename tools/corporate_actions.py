import requests
import re
import difflib
from bs4 import BeautifulSoup
from db_setup.portfolio_manager_setup import get_db_connection, init_db

def _sync_live_announcements() -> dict:
    """
    Core Logic: Scrapes PSX announcements, uses fuzzy matching to find the 
    official ticker from the DB, and logs new entries with an unapplied (0) status.
    """
    init_db()
    url = "https://www.psx.com.pk/psx/announcement/financial-announcements"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        return {"status": "error", "message": f"Failed to fetch live page: {e}"}

    soup = BeautifulSoup(response.text, "html.parser")
    tables = soup.find_all("table")
    
    # --- LOAD OFFICIAL TICKER MAP FOR FUZZY MATCHING ---
    official_mapping = {}
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT ticker, company_name FROM ticker_mapping')
        for row in cursor.fetchall():
            official_mapping[row['company_name']] = row['ticker']
            
    company_names_list = list(official_mapping.keys())
    
    saved_count = 0
    logged_actions = []

    for table in tables:
        headers_row = table.find("tr")
        if not headers_row or "dividend" not in headers_row.get_text(strip=True).lower():
            continue
            
        rows = table.find_all("tr")[1:]
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 9:
                continue
                
            raw_company_name = cols[0].get_text(strip=True)
            
            # Fuzzy matching logic
            best_matches = difflib.get_close_matches(raw_company_name, company_names_list, n=1, cutoff=0.6)
            if best_matches:
                official_name = best_matches[0]
                ticker = official_mapping[official_name]
            else:
                ticker = raw_company_name.split()[0].upper()
                
            payout_info = cols[3].get_text(strip=True)
            book_closure = cols[8].get_text(strip=True)
            
            if not payout_info or payout_info in ["-", "nil"]:
                continue
                
            # Parse Date
            date_match = re.search(r'(\d{2})/(\d{2})/(\d{4})', book_closure)
            if date_match:
                ex_date = f"{date_match.group(3)}-{date_match.group(2)}-{date_match.group(1)}"
            else:
                ex_date = "0000-00-00" 

            # Extract Percentage
            num_match = re.search(r'(\d+(?:\.\d+)?)%', payout_info)
            if not num_match:
                continue
            percentage_val = float(num_match.group(1))

            # Categorize Action Type
            action_type = None
            amount_or_ratio = 0.0
            
            if "(D)" in payout_info:
                action_type = "cash_dividend"
                amount_or_ratio = (percentage_val / 100.0) * 10.0 
            elif "(B)" in payout_info:
                action_type = "bonus_issue"
                amount_or_ratio = percentage_val / 100.0 
            elif "(R)" in payout_info:
                action_type = "right_issue"
                amount_or_ratio = percentage_val / 100.0 

            # Check duplication and record
            if action_type:
                history = _get_action_history(ticker)
                is_duplicate = any(
                    item['action_type'] == action_type and item['ex_date'] == ex_date 
                    for item in history.get('history', [])
                )
                
                if not is_duplicate:
                    _record_action(ticker, action_type, amount_or_ratio, ex_date)
                    saved_count += 1
                    logged_actions.append({
                        "ticker": ticker,
                        "type": action_type,
                        "value": amount_or_ratio,
                        "ex_date": ex_date
                    })
                        
        break 

    return {
        "status": "success",
        "new_records_saved": saved_count,
        "saved_actions": logged_actions
    }

def _record_action(ticker: str, action_type: str, amount_or_ratio: float, ex_date: str) -> dict:
    ticker = ticker.upper()
    action_type = action_type.lower()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO corporate_actions (ticker, action_type, amount_or_ratio, ex_date, applied)
            VALUES (?, ?, ?, ?, 0)
        ''', (ticker, action_type, amount_or_ratio, ex_date))
        conn.commit()
        action_id = cursor.lastrowid
        
    return {
        "status": "success",
        "id": action_id,
        "message": f"Recorded {action_type} for {ticker}."
    }

def _apply_pending_actions() -> dict:
    """Processes pending corporate events and sets applied flag to 1."""
    applied_actions = []
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM corporate_actions WHERE applied = 0')
        pending = cursor.fetchall()
        
        for row in pending:
            action_dict = dict(row)
            
            # Portfolio execution hooking point (e.g., cash adjusting)
            
            cursor.execute('UPDATE corporate_actions SET applied = 1 WHERE id = ?', (row['id'],))
            action_dict['applied'] = True 
            applied_actions.append(action_dict)
            
        conn.commit()
        
    return {
        "status": "success",
        "actions_applied_count": len(applied_actions),
        "details": applied_actions
    }

def _get_action_history(ticker: str = None) -> dict:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if ticker:
            cursor.execute('SELECT * FROM corporate_actions WHERE ticker = ? ORDER BY ex_date DESC', (ticker.upper(),))
        else:
            cursor.execute('SELECT * FROM corporate_actions ORDER BY ex_date DESC')
            
        history = [dict(row) for row in cursor.fetchall()]
        for item in history:
            item['applied'] = bool(item['applied'])
            
    return {
        "status": "success",
        "record_count": len(history),
        "history": history
    }