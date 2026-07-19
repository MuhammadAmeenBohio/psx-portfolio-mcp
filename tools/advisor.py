def _analyze_holding(
    ticker: str, 
    market_price: float, 
    fundamental_value: float, 
    inflation_rate: float, 
    nominal_yield: float
) -> dict:
    """
    Synthesizes market price, fundamental value (NAV or Intrinsic Value), and macro 
    inflation data to generate a holistic advisory holding report.

    Args:
        ticker (str): The symbol of the asset.
        market_price (float): The current live trading price.
        fundamental_value (float): The target value (iNAV for ETFs, Intrinsic Value for equities).
        inflation_rate (float): The current annualized inflation rate (e.g., 12.5 for 12.5%).
        nominal_yield (float): The expected dividend or distribution yield (e.g., 8.0 for 8.0%).

    Returns:
        dict: A synthesized advisory report containing upside potential, real yield, 
              and an automated conviction signal.
    """
    if market_price <= 0:
        return {
            "status": "error", 
            "message": "Market price must be strictly greater than zero to analyze upside."
        }
        
    price_deviation = fundamental_value - market_price
    upside_potential_pct = (price_deviation / market_price) * 100
    
    real_yield = nominal_yield - inflation_rate
    breakeven_appreciation_needed = max(0.0, inflation_rate - nominal_yield)
    
    if upside_potential_pct > 5 and real_yield > 0:
        conviction = "Strong Buy (Inflation Beating & Undervalued)"
    elif upside_potential_pct > 0 or real_yield >= 0:
        conviction = "Hold / Accumulate"
    else:
        conviction = "Underweight / Sell (Eroding Purchasing Power)"
        
    return {
        "status": "success",
        "module": "Advisor Synthesis",
        "data": {
            "ticker": ticker.upper().strip(),
            "valuation_metrics": {
                "market_price": market_price,
                "fundamental_target": fundamental_value,
                "upside_potential_pct": round(upside_potential_pct, 2)
            },
            "macro_overlay": {
                "inflation_rate_pct": inflation_rate,
                "nominal_yield_pct": nominal_yield,
                "real_yield_pct": round(real_yield, 2),
                "appreciation_needed_for_inflation_breakeven_pct": round(breakeven_appreciation_needed, 2)
            },
            "synthesized_signal": conviction
        }
    }

from datetime import datetime

def _calculate_xirr(cash_flows: list[dict], guess: float = 0.1) -> float:
    """
    Safely approximates the Extended Internal Rate of Return (XIRR) using the Secant method.
    cash_flows must contain dicts with 'date' (YYYY-MM-DD) and 'amount' (float).
    """
    try:
        amounts = [cf["amount"] for cf in cash_flows]
        # Safeguard: XIRR requires at least one positive and one negative cash flow
        if min(amounts) >= 0 or max(amounts) <= 0:
            return None

        cfs = []
        for cf in cash_flows:
            dt = datetime.strptime(cf["date"], "%Y-%m-%d")
            cfs.append((dt, cf["amount"]))
        
        cfs.sort(key=lambda x: x[0])
        t0 = cfs[0][0]

        def xnpv(r):
            if r <= -1.0:
                return float('inf') # Prevent complex numbers / division by zero
            return sum([amt / ((1.0 + r) ** ((dt - t0).days / 365.25)) for dt, amt in cfs])

        x0 = guess
        x1 = guess + 0.05
        
        # Secant method with 100 iteration safeguard
        for _ in range(100):
            f0 = xnpv(x0)
            f1 = xnpv(x1)
            if f1 == f0:
                break
            x_next = x1 - f1 * (x1 - x0) / (f1 - f0)
            if abs(x_next - x1) < 1e-5:
                return x_next
            x0 = x1
            x1 = x_next
            
        return None # Failed to converge
    except Exception:
        return None

def _portfolio_health_check(holdings: list[dict], cash_flows: list[dict] = None) -> dict:
    """
    Evaluates portfolio health by analyzing asset allocation, concentration risk, and XIRR.

    Args:
        holdings (list[dict]): List of assets. Expected format: [{'ticker': 'ENGRO', 'value': 50000}, ...]
        cash_flows (list[dict], optional): List of portfolio cash flows for XIRR calculation. 
                                           Expected format: [{'date': '2025-01-01', 'amount': -50000}, ...]

    Returns:
        dict: A standardized dictionary containing total value, allocation percentages, 
              concentration risk flags, XIRR, and an overall health status flag.
    """
    if not holdings:
        return {"status": "error", "message": "Holdings list cannot be empty."}

    total_value = sum(h.get("value", 0.0) for h in holdings)
    
    if total_value <= 0:
        return {"status": "error", "message": "Total portfolio value must be greater than zero."}

    # 1. Allocation & Concentration Analysis
    allocations = []
    for h in holdings:
        ticker = h.get("ticker", "UNKNOWN").upper()
        val = h.get("value", 0.0)
        weight = (val / total_value) * 100
        allocations.append({
            "ticker": ticker,
            "value": val,
            "weight_pct": round(weight, 2)
        })

    # Sort descending by weight
    allocations.sort(key=lambda x: x["weight_pct"], reverse=True)
    top_holding = allocations[0]
    
    concentration_flag = "Safe"
    if top_holding["weight_pct"] >= 40:
        concentration_flag = "Critical Concentration Risk"
    elif top_holding["weight_pct"] >= 20:
        concentration_flag = "Moderate Concentration Risk"

    # 2. XIRR Calculation (if cash flows provided)
    portfolio_xirr = None
    if cash_flows and len(cash_flows) > 1:
        raw_xirr = _calculate_xirr(cash_flows)
        if raw_xirr is not None:
            portfolio_xirr = round(raw_xirr * 100, 2)

    # 3. Synthesize Overall Health Status
    health_status = "Healthy"
    if concentration_flag != "Safe":
        health_status = f"Warning: {concentration_flag} ({top_holding['ticker']} at {top_holding['weight_pct']}%)"
    if portfolio_xirr is not None and portfolio_xirr < 0:
        health_status = "Warning: Negative Time-Weighted Return (XIRR) combined with " + concentration_flag

    return {
        "status": "success",
        "module": "Portfolio Health Diagnostics",
        "data": {
            "total_portfolio_value": round(total_value, 2),
            "concentration_status": concentration_flag,
            "xirr_pct": portfolio_xirr,
            "top_holding_ticker": top_holding["ticker"],
            "top_holding_weight_pct": top_holding["weight_pct"],
            "allocations": allocations,
            "synthesized_health_signal": health_status
        }
    }