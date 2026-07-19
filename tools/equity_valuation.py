import psxdata
import pandas as pd
from datetime import datetime, timedelta
from .market import _search_ticker

def _get_etf_data(query: str, start_date: str, end_date: str) -> dict:
    """
    Dedicated helper to fetch historical data specifically for Exchange Traded Funds (ETFs).
    Resolves the query, fetches records, and guarantees strict chronological sorting.
    """
    search_result = _search_ticker(query)
    
    if search_result.get("status") != "success" or not search_result.get("matches"):
        return {"error": f"Could not find an official ETF matching '{query}'."}
        
    ticker = search_result["matches"][0]["ticker"]
        
    try:
        df = psxdata.stocks(ticker, start=start_date, end=end_date)
        
        if df is None or df.empty:
            return {"error": f"No trading data found for ETF {ticker} within the requested dates."}
            
        date_col = 'date' if 'date' in df.columns else 'Date'
        
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(by=date_col, ascending=True)
        df[date_col] = df[date_col].dt.strftime('%Y-%m-%d')
        
        if 'index' in df.columns:
            df = df.drop(columns=['index'])
            
        return {
            "status": "success",
            "etf_ticker": ticker, 
            "etf_name": search_result["matches"][0]["company_name"],
            "total_records": len(df),
            "history": df.to_dict(orient="records")
        }
        
    except Exception as e:
        return {"error": f"Failed to pull ETF metrics from data layer: {str(e)}"}
    
def _value_stock_ddm(dividend: float, required_return: float, growth_rate: float, ticker: str = None) -> dict:
    """
    Calculates the fair value of a stock using the Gordon Growth Model (DDM).
    """
    try:
        if required_return <= growth_rate:
            return {
                "status": "error", 
                "message": "Model failed: The required rate of return (r) must be strictly greater than the perpetual growth rate (g)."
            }
            
        fair_value = dividend / (required_return - growth_rate)
        
        result = {
            "status": "success",
            "model": "Gordon Growth Model (DDM)",
            "inputs": {
                "expected_dividend_d1": dividend,
                "required_return": required_return,
                "growth_rate": growth_rate
            },
            "fair_value": round(fair_value, 2)
        }
        
        if ticker:
            result["ticker"] = str(ticker).upper()
            
        return result
        
    except ZeroDivisionError:
        return {"status": "error", "message": "Division by zero occurred. Check your return and growth rate inputs."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to calculate DDM valuation: {str(e)}"}
    
def _value_stock_two_stage_ddm(
    current_dividend: float, 
    required_return: float, 
    high_growth_rate: float, 
    high_growth_years: int, 
    stable_growth_rate: float, 
    ticker: str = None
) -> dict:
    """
    Calculates the fair value of a stock using the Two-Stage Dividend Discount Model.
    Accounts for a high-growth phase followed by a perpetual stable-growth phase.
    """
    try:
        if required_return <= stable_growth_rate:
            return {
                "status": "error", 
                "message": "Model failed: The required rate of return (r) must be strictly greater than the stable growth rate."
            }

        present_value_dividends = 0.0
        current_d = current_dividend

        for t in range(1, high_growth_years + 1):
            current_d *= (1 + high_growth_rate)
            present_value_dividends += current_d / ((1 + required_return) ** t)

        dividend_terminal = current_d * (1 + stable_growth_rate)
        terminal_value = dividend_terminal / (required_return - stable_growth_rate)
        
        present_value_terminal = terminal_value / ((1 + required_return) ** high_growth_years)

        fair_value = present_value_dividends + present_value_terminal

        result = {
            "status": "success",
            "model": "Two-Stage DDM",
            "inputs": {
                "current_dividend_d0": current_dividend,
                "required_return": required_return,
                "high_growth_rate": high_growth_rate,
                "high_growth_years": high_growth_years,
                "stable_growth_rate": stable_growth_rate
            },
            "fair_value": round(fair_value, 2)
        }

        if ticker:
            result["ticker"] = str(ticker).upper()

        return result

    except Exception as e:
        return {"status": "error", "message": f"Failed to calculate Two-Stage DDM: {str(e)}"}
    
def _value_stock_pe(eps: float, target_pe: float, ticker: str = None) -> dict:
    """
    Calculates the implied fair value of a stock using a target Price-to-Earnings (P/E) ratio.
    Often used with an industry average P/E to see if a stock is relatively undervalued.
    """
    try:
        if eps <= 0:
            return {
                "status": "error",
                "message": "Model failed: Relative P/E valuation requires positive Earnings Per Share (EPS). The company is currently operating at a loss."
            }
            
        if target_pe <= 0:
            return {
                "status": "error",
                "message": "Model failed: The target P/E ratio must be a positive number."
            }

        fair_value = eps * target_pe

        result = {
            "status": "success",
            "model": "Relative Valuation (P/E Multiple)",
            "inputs": {
                "earnings_per_share": eps,
                "target_pe_ratio": target_pe
            },
            "fair_value": round(fair_value, 2)
        }

        if ticker:
            result["ticker"] = str(ticker).upper()

        return result

    except Exception as e:
        return {"status": "error", "message": f"Failed to calculate P/E valuation: {str(e)}"}
    
def _value_stock_dcf(
    projected_fcfs: list, 
    wacc: float, 
    terminal_growth_rate: float, 
    net_debt: float = 0.0, 
    shares_outstanding: float = None, 
    ticker: str = None
) -> dict:
    """
    Calculates the intrinsic value of a company using a multi-period Discounted Cash Flow (DCF) model.
    Discounts projected Free Cash Flows and terminal value back to present value using WACC.
    """
    try:
        if wacc <= terminal_growth_rate:
            return {
                "status": "error",
                "message": "Model failed: The discount rate (WACC) must be strictly greater than the terminal growth rate."
            }
            
        if not projected_fcfs:
            return {
                "status": "error",
                "message": "Model failed: You must provide a list of projected Free Cash Flows (FCFs)."
            }

        pv_of_fcfs = []
        for i, fcf in enumerate(projected_fcfs):
            year = i + 1
            pv = fcf / ((1 + wacc) ** year)
            pv_of_fcfs.append(pv)
            
        total_pv_fcfs = sum(pv_of_fcfs)

        last_fcf = projected_fcfs[-1]
        terminal_value = (last_fcf * (1 + terminal_growth_rate)) / (wacc - terminal_growth_rate)
        
        projection_years = len(projected_fcfs)
        pv_of_terminal_value = terminal_value / ((1 + wacc) ** projection_years)

        enterprise_value = total_pv_fcfs + pv_of_terminal_value
        equity_value = enterprise_value - net_debt

        result = {
            "status": "success",
            "model": "Discounted Cash Flow (DCF)",
            "projection_years": projection_years,
            "valuation_breakdown": {
                "pv_of_interim_fcfs": round(total_pv_fcfs, 2),
                "pv_of_terminal_value": round(pv_of_terminal_value, 2),
                "enterprise_value": round(enterprise_value, 2),
                "equity_value": round(equity_value, 2)
            }
        }

        if shares_outstanding and shares_outstanding > 0:
            fair_value_per_share = equity_value / shares_outstanding
            result["fair_value_per_share"] = round(fair_value_per_share, 2)
        else:
            result["fair_value_per_share"] = None
            result["note"] = "Provide 'shares_outstanding' to compute the exact per-share intrinsic value."

        if ticker:
            result["ticker"] = str(ticker).upper()

        return result

    except Exception as e:
        return {"status": "error", "message": f"Failed to calculate DCF model: {str(e)}"}
    
def _calculate_dividend_yield(annual_dividend: float, current_price: float, ticker: str = None) -> dict:
    """
    Calculates the dividend yield of a stock.
    Returns both the raw decimal for further calculations and a formatted percentage string.
    """
    try:
        if current_price <= 0:
            return {
                "status": "error",
                "message": "Model failed: The current price must be greater than zero to calculate yield."
            }
            
        if annual_dividend < 0:
            return {
                "status": "error",
                "message": "Model failed: Annual dividend cannot be a negative number."
            }

        yield_decimal = annual_dividend / current_price

        result = {
            "status": "success",
            "model": "Dividend Yield",
            "inputs": {
                "annual_dividend": annual_dividend,
                "current_price": current_price
            },
            "dividend_yield_decimal": round(yield_decimal, 4),
            "dividend_yield_percentage": f"{round(yield_decimal * 100, 2)}%"
        }

        if ticker:
            result["ticker"] = str(ticker).upper()

        return result

    except Exception as e:
        return {"status": "error", "message": f"Failed to calculate dividend yield: {str(e)}"}
    
def _compare_peer_valuation(peers_data: list[dict]) -> dict:
    """
    Compares valuation metrics (P/E, P/B, Dividend Yield, Market Cap) across a group of peers.
    Automatically calculates peer averages and determines relative valuation standing.
    """
    try:
        if not peers_data or len(peers_data) < 1:
            return {
                "status": "error",
                "message": "Model failed: You must provide a list containing metrics for at least one ticker."
            }

        valid_pe = [p["pe"] for p in peers_data if p.get("pe") is not None and p["pe"] > 0]
        valid_pb = [p["pb"] for p in peers_data if p.get("pb") is not None and p["pb"] > 0]
        valid_yield = [p["dividend_yield"] for p in peers_data if p.get("dividend_yield") is not None]
        valid_cap = [p["market_cap"] for p in peers_data if p.get("market_cap") is not None]

        averages = {
            "pe_average": round(sum(valid_pe) / len(valid_pe), 2) if valid_pe else None,
            "pb_average": round(sum(valid_pb) / len(valid_pb), 2) if valid_pb else None,
            "dividend_yield_average_pct": f"{round((sum(valid_yield) / len(valid_yield)) * 100, 2)}%" if valid_yield else None,
            "market_cap_average": round(sum(valid_cap) / len(valid_cap), 2) if valid_cap else None
        }

        avg_yield_raw = sum(valid_yield) / len(valid_yield) if valid_yield else 0.0

        comparison_matrix = []
        for peer in peers_data:
            ticker = str(peer.get("ticker", "UNKNOWN")).upper()
            pe = peer.get("pe")
            pb = peer.get("pb")
            div_yield = peer.get("dividend_yield", 0.0)
            market_cap = peer.get("market_cap")

            status_flags = []
            if pe and averages["pe_average"]:
                status_flags.append("Discount P/E" if pe < averages["pe_average"] else "Premium P/E")
            if pb and averages["pb_average"]:
                status_flags.append("Discount P/B" if pb < averages["pb_average"] else "Premium P/B")
            if div_yield and avg_yield_raw:
                status_flags.append("High Yield" if div_yield > avg_yield_raw else "Low Yield")

            comparison_matrix.append({
                "ticker": ticker,
                "pe": pe,
                "pb": pb,
                "dividend_yield_pct": f"{round(div_yield * 100, 2)}%",
                "market_cap": market_cap,
                "analysis_tags": status_flags
            })

        return {
            "status": "success",
            "peer_count": len(peers_data),
            "group_benchmarks": averages,
            "comparison_matrix": comparison_matrix
        }

    except Exception as e:
        return {"status": "error", "message": f"Failed to generate peer comparison matrix: {str(e)}"}
    
_ETF_INAV_CACHE = {}
_INAV_CACHE_TTL_SECONDS = 15  

def _get_etf_inav(ticker: str) -> dict:
    """
    Internal worker to fetch the Indicative Net Asset Value (iNAV) and market quote for a given ETF.
    Implements a 15-second in-memory cache and a historical data fallback to prevent brittle API failures.

    Args:
        ticker (str): The official ETF symbol on the PSX (e.g., 'MZNPETF', 'UBLPETF').

    Returns:
        dict: A standardized dictionary containing the ETF's pricing data, the source of the data 
              (cache, live, or fallback), and a success/error status.
    """
    ticker = ticker.upper().strip()
    now = datetime.now()
    
    if ticker in _ETF_INAV_CACHE:
        cache_entry = _ETF_INAV_CACHE[ticker]
        time_elapsed = (now - cache_entry['timestamp']).total_seconds()
        
        if time_elapsed < _INAV_CACHE_TTL_SECONDS:
            return {
                "status": "success",
                "source": "memory_cache",
                "ticker": ticker,
                "data": cache_entry['data'],
                "message": f"Retrieved from local cache ({int(time_elapsed)}s old)"
            }
            
    try:
        quote = psxdata.quote(ticker)
        quote_dict = {}
        source_label = "psxdata_live_quote"
        
        if quote is None or (isinstance(quote, pd.DataFrame) and quote.empty):
            start_date = (now - timedelta(days=7)).strftime("%Y-%m-%d")
            end_date = now.strftime("%Y-%m-%d")
            
            history = psxdata.stocks(ticker, start=start_date, end=end_date)
            
            if history is None or (isinstance(history, pd.DataFrame) and history.empty):
                 return {
                     "status": "error", 
                     "message": f"Exchange returned no live or historical data for ETF: {ticker}"
                 }
            
            if isinstance(history.index, pd.DatetimeIndex):
                history = history.sort_index()
                latest_date_str = str(history.index[-1].date())
            else:
                date_col = history.columns[0] 
                history[date_col] = pd.to_datetime(history[date_col])
                history = history.sort_values(by=date_col)
                latest_date_str = str(history.iloc[-1][date_col].date())
            
            latest_row = history.iloc[-1].to_dict()
            
            quote_dict = {
                "Price": latest_row.get('Close', latest_row.get('close', 0)),
                "Volume": latest_row.get('Volume', latest_row.get('volume', 0)),
                "Date_Proxy": latest_date_str
            }
            source_label = "psxdata_historical_fallback"
            
        else:
            if isinstance(quote, pd.DataFrame):
                quote_dict = quote.iloc[0].to_dict()
            else:
                quote_dict = quote.to_dict()
        
        _ETF_INAV_CACHE[ticker] = {
            "timestamp": now,
            "data": quote_dict
        }
        
        return {
            "status": "success",
            "source": source_label,
            "ticker": ticker,
            "data": quote_dict,
            "message": "Successfully fetched ETF pricing data."
        }
        
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Failed to fetch data for {ticker}. Error: {str(e)}"
        }
    
def _calculate_etf_premium_discount(market_price: float, inav: float) -> dict:
    """
    Calculates the premium or discount of an ETF's market price relative to its iNAV.
    Includes mathematical safeguards against zero division and negative prices.

    Args:
        market_price (float): The current live trading price of the ETF.
        inav (float): The current Indicative Net Asset Value (iNAV) of the ETF.

    Returns:
        dict: A standardized dictionary containing the absolute difference, percentage 
              deviation, and a trading status flag (Premium, Discount, or Par).
    """
    if inav <= 0:
        return {
            "status": "error", 
            "message": "iNAV must be strictly greater than zero to calculate deviation."
        }
        
    if market_price < 0:
        return {
            "status": "error",
            "message": "Market price cannot be negative."
        }

    difference = market_price - inav
    percentage_deviation = (difference / inav) * 100
    
    if difference > 0:
        trading_status = "Premium"
    elif difference < 0:
        trading_status = "Discount"
    else:
        trading_status = "Par"

    return {
        "status": "success",
        "model": "ETF Premium/Discount to iNAV",
        "data": {
            "market_price_used": market_price,
            "inav_used": inav,
            "absolute_difference": round(difference, 4),
            "percentage_deviation": round(percentage_deviation, 4),
            "trading_status": trading_status
        }
    }

def _calculate_etf_tracking_difference(etf_return: float, benchmark_return: float) -> dict:
    """
    Calculates the tracking difference between an ETF's realized return and its underlying benchmark.

    Args:
        etf_return (float): The realized return of the ETF over a specific period (e.g., 5.2 for 5.2%).
        benchmark_return (float): The realized return of the benchmark index over the same period.

    Returns:
        dict: A standardized dictionary containing the absolute tracking difference and 
              a performance status flag indicating underperformance or outperformance.
    """
    difference = etf_return - benchmark_return
    
    if difference > 0:
        performance_status = "Outperformance"
    elif difference < 0:
        performance_status = "Underperformance"
    else:
        performance_status = "Exact Match"

    return {
        "status": "success",
        "model": "ETF Tracking Difference",
        "data": {
            "etf_return_used": etf_return,
            "benchmark_return_used": benchmark_return,
            "tracking_difference": round(difference, 4),
            "performance_status": performance_status
        }
    }