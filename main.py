from tools.tvm import *
from tools.inflation import (check_inflation_rate,
                              override_inflation_rate,
                              real_return,
                              future_cost)
from tools.corporate_actions import(
    _sync_live_announcements,
    _record_action,
    _apply_pending_actions,
    _get_action_history
)

from tools.market import (
    _fetch_stock_quote,
    _search_ticker,
    _get_historical_prices,
    _list_tickers,
    _get_index_constituents,
    _get_sector_summary,
    _search_ticker
)

from tools.equity_valuation import (
    _get_etf_data,
    _value_stock_ddm,
    _value_stock_two_stage_ddm,
    _value_stock_pe,
    _value_stock_dcf,
    _calculate_dividend_yield,
    _compare_peer_valuation,
    _get_etf_inav,
    _calculate_etf_premium_discount,
    _calculate_etf_tracking_difference
)

from tools.advisor import (
    _analyze_holding,
    _portfolio_health_check
)

from fastmcp import FastMCP

mcp = FastMCP(name= "psx-analyzer")

#=========================================================
#                        TVM TOOLS
#=========================================================

@mcp.tool
def calculate_fv(
    principle: float,
    annual_rate: float,
    compounding: str,
    years: float
):
    """Calculate the future value of lump sum investment with compounding.

    Args:
        principal (float): The initial lump sum of money today.
        annual_rate (float): The annual interest rate (expressed as a percentage, e.g., 5.0 for 5%).
        compounding (str): The frequency of compounding. 
                           Accepted values: "annually", "semi_annually", "quarterly", "monthly", "daily".
        years (float): The number of years the money is invested.

    Returns:
        dict: A dictionary containing the calculated future value (e.g., {"future_value": 1628.89}).
    """
    return future_value(principle, annual_rate, compounding, years)


@mcp.tool
def calculate_pv(
    future_value: float,
    annual_rate: float,
    compounding: str,
    years: float
) -> dict:
    """Calculate the present value of a future lump sum with compounding.

    Args:
        future_value (float): The amount of money expected in the future.
        annual_rate (float): The annual interest rate (expressed as a percentage, e.g., 5.0 for 5%).
        compounding (str): The frequency of compounding. 
                           Accepted values: "annually", "semi_annually", "quarterly", "monthly", "daily".
        years (float): The number of years until the money is received.

    Returns:
        dict: A dictionary containing the calculated present value (e.g., {"present_value": 7835.26}).
    """
    return present_value(future_value=future_value, annual_rate=annual_rate, compounding=compounding, years=years)


@mcp.tool
def calculate_annuity_fv(
    payment: float,
    annual_rate: float,
    compounding: str,
    years: float,
    payment_timing: str = "end"
) -> dict:
    """Calculate the future value of recurring payments (an annuity).

    Args:
        payment (float): The amount of money paid at each regular interval.
        annual_rate (float): The annual interest rate (expressed as a percentage, e.g., 5.0 for 5%).
        compounding (str): The frequency of the payments and compounding. 
                           Accepted values: "annually", "semi_annually", "quarterly", "monthly", "daily".
        years (float): The number of years the payments are made.
        payment_timing (str): When the payment is made. 
                              Use "end" for Ordinary Annuity or "begin" for Annuity Due. Defaults to "end".

    Returns:
        dict: A dictionary containing the calculated future value of the annuity (e.g., {"future_value_annuity": 15528.23}).
    """
    return annuity_fv(
        payment=payment, 
        annual_rate=annual_rate, 
        compounding=compounding, 
        years=years, 
        payment_timing=payment_timing
    )

@mcp.tool
def calculate_annuity_pv(
    payment: float,
    annual_rate: float,
    compounding: str,
    years: float,
    payment_timing: str = "end"
) -> dict:
    """Calculate the present value of recurring payments (an annuity).

    Args:
        payment (float): The amount of money paid at each regular interval.
        annual_rate (float): The annual interest rate (expressed as a percentage, e.g., 5.0 for 5%).
        compounding (str): The frequency of the payments and compounding. 
                           Accepted values: "annually", "semi_annually", "quarterly", "monthly", "daily".
        years (float): The number of years the payments are made.
        payment_timing (str): When the payment is made. 
                              Use "end" for Ordinary Annuity or "begin" for Annuity Due. Defaults to "end".

    Returns:
        dict: A dictionary containing the calculated present value of the annuity (e.g., {"present_value_annuity": 10379.66}).
    """
    return annuity_pv(
        payment=payment, 
        annual_rate=annual_rate, 
        compounding=compounding, 
        years=years, 
        payment_timing=payment_timing
    )

@mcp.tool
def calculate_perpetuity(
    payment: float,
    annual_rate: float,
    compounding: str = "annually",
    growth_rate: float = 0.0
) -> dict:
    """Calculate the present value of an infinite payment stream (perpetuity) with optional growth.

    Args:
        payment (float): The amount of money paid at each regular interval.
        annual_rate (float): The annual interest/discount rate (expressed as a percentage, e.g., 5.0 for 5%).
        compounding (str, optional): The frequency of the payments. 
                                     Accepted values: "annually", "semi_annually", "quarterly", "monthly", "daily". 
        growth_rate (float, optional): The annual growth rate of the payment (expressed as a percentage, e.g., 2.0 for 2%). 
                                       Defaults to 0.0.

    Returns:
        dict: A dictionary containing the calculated present value of the perpetuity (e.g., {"present_value_perpetuity": 20000.0}).
    """
    return perpetuity_pv(
        payment=payment, 
        annual_rate=annual_rate, 
        compounding=compounding, 
        growth_rate=growth_rate
    )

@mcp.tool
def calculate_rule_of_72(annual_rate: float) -> dict:
    """Calculate the estimated (Rule of 72) and exact time required for an investment to double.

    Args:
        annual_rate (float): The annual interest rate (expressed as a percentage, e.g., 8.0 for 8%).

    Returns:
        dict: A dictionary containing the estimated years, exact years, and the difference between them.
              (e.g., {"rule_of_72_estimate_years": 9.0, "exact_doubling_years": 9.006, "difference_years": 0.006}).
    """
    return rule_of_72(annual_rate=annual_rate)

@mcp.tool
def calculate_effective_rate(nominal_rate: float, compounding: str) -> dict:
    """Calculate the Effective Annual Rate (EAR) from a nominal interest rate.

    Args:
        nominal_rate (float): The stated annual interest rate (expressed as a percentage, e.g., 5.0 for 5%).
        compounding (str): The frequency of compounding. 
                           Accepted values: "annually", "semi_annually", "quarterly", "monthly", "daily".

    Returns:
        dict: A dictionary containing the true effective annual rate as a percentage 
              (e.g., {"effective_rate": 5.116189}).
    """
    return effective_rate(nominal_rate=nominal_rate, compounding=compounding)

@mcp.tool
def calculate_savings_needed(
    target_amount: float,
    years: float,
    annual_rate: float,
    current_savings: float = 0.0,
    compounding: str = "monthly"
) -> dict:
    """Calculate the regular contribution needed to reach a specific financial goal.

    Args:
        target_amount (float): The final amount of money you want to have (your goal).
        years (float): The number of years you have to save.
        annual_rate (float): The expected annual return/interest rate (expressed as a percentage, e.g., 7.0 for 7%).
        current_savings (float, optional): The amount of money you already have saved.
        compounding (str, optional): The frequency of contributions and compounding. 
                                     Accepted values: "annually", "semi_annually", "quarterly", "monthly", "daily". 

    Returns:
        dict: A dictionary containing the required payment per period (e.g., {"payment_needed": 500.50}).
    """
    return savings_needed(
        target_amount=target_amount, 
        years=years, 
        annual_rate=annual_rate, 
        current_savings=current_savings, 
        compounding=compounding
    )

#=========================================================
#                     INFLATION TOOLS
#=========================================================

@mcp.tool
def get_inflation_rate() -> dict:
    """Gets the current Pakistan CPI inflation rate using a cache-first approach.

    Returns:
        dict: A dictionary containing the inflation rate, the data source, and a 
              flag indicating if the cached data is stale (older than 24 hours).
              (e.g., {"inflation_rate": 11.7, "source": "cache", "is_stale": False})
    """
    return check_inflation_rate()

@mcp.tool
def set_inflation_rate(manual_rate: float) -> dict:
    """Manual override to set the current inflation rate in the cache.

    Args:
        manual_rate (float): The new inflation rate to store (expressed as a percentage, e.g., 12.5).

    Returns:
        dict: A confirmation dictionary with the updated rate and status.
    """
    return override_inflation_rate(manual_rate=manual_rate)

@mcp.tool
def calculate_real_return(nominal_rate: float, inflation_rate: float = None) -> dict:
    """Calculate the real rate of return of an investment using the Fisher equation.
    
    If no inflation rate is explicitly provided, the tool automatically fetches 
    the current Pakistan CPI inflation rate from the macro cache or live source.

    Args:
        nominal_rate (float): The nominal return or interest rate (expressed as a percentage, e.g., 15.0 for 15%).
        inflation_rate (float, optional): The inflation rate (expressed as a percentage). 
                                       If omitted, defaults to auto-fetching live/cached macro data.

    Returns:
        dict: A dictionary containing exact and approximate real returns alongside the inflation source used.
    """
    return real_return(nominal_rate=nominal_rate, inflation_rate=inflation_rate)

@mcp.tool
def project_future_cost(current_cost: float, years: float, inflation_rate: float = None) -> dict:
    """Project the future cost of today's expense adjusted for expected inflation.
    
    If no inflation rate is explicitly provided, the tool automatically fetches 
    the current Pakistan CPI inflation rate from the macro cache or live source.

    Args:
        current_cost (float): The price of the item or expense today.
        years (float): The number of years into the future to project.
        inflation_rate (float, optional): The expected annual inflation rate (expressed as a percentage, e.g., 11.7). 
                                       If omitted, defaults to auto-fetching live/cached macro data.

    Returns:
        dict: A dictionary containing the projected future cost alongside the parameters used 
              (e.g., {"projected_cost": 1500.50, "inflation_source": "auto_fetched (cache)"}).
    """
    return future_cost(current_cost=current_cost, years=years, inflation_rate=inflation_rate)

#=========================================================
#                     CORPORATE TOOLS
#=========================================================

@mcp.tool
def sync_live_corporate_actions() -> dict:
    """Scrapes the live PSX financial announcements page, parses the latest dividends, 
    bonuses, and rights issues, and automatically logs any new entries into the database.
    If the local database does not exist yet (cold start), it will automatically create 
    and initialize it before saving the data.

    Returns:
        dict: A status summary detailing the number of new records successfully saved.
    """
    return _sync_live_announcements()

@mcp.tool
def record_corporate_action(ticker: str, action_type: str, amount_or_ratio: float, ex_date: str) -> dict:
    """Record a new corporate action (dividend, bonus, split) into the database.

    Args:
        ticker (str): The stock symbol (e.g., 'ENGRO', 'HUBC').
        action_type (str): The type of action ('cash_dividend', 'bonus_issue', 'stock_split', 'right_issue').
        amount_or_ratio (float): The rupee amount for cash dividends, or ratio for splits/bonuses.
        ex_date (str): The Ex-Dividend/Ex-Entitlement date in YYYY-MM-DD format.

    Returns:
        dict: A confirmation with the database row ID.
    """
    return _record_action(ticker, action_type, amount_or_ratio, ex_date)

@mcp.tool
def apply_pending_corporate_actions() -> dict:
    """Scan the database for unapplied corporate actions and mark them as applied.

    Returns:
        dict: A summary of the actions that were successfully applied.
    """
    return _apply_pending_actions()

@mcp.tool
def get_corporate_action_history(ticker: str = None) -> dict:
    """Retrieve the history of recorded corporate actions.

    Args:
        ticker (str, optional): Pass a specific ticker to filter the history.

    Returns:
        dict: A list of historical corporate actions.
    """
    return _get_action_history(ticker)

#=========================================================
#                      MARKET TOOLS
#=========================================================

@mcp.tool
def get_quote(ticker: str) -> dict:
    """Gets a real time financial screener snapshot for a given PSX stock ticker.
    Includes the current price, P/E ratio, dividend yield, and market capitalization.

    Args:
        ticker (str): The stock symbol to look up (e.g., 'ENGRO', 'HUBC', 'MEBL').

    Returns:
        dict: A dictionary containing the normalized live stock snapshot data.
    """
    return _fetch_stock_quote(ticker)

@mcp.tool()
def search_ticker(query: str) -> dict:
    """
    Searches for a company's ticker symbol on the Pakistan Stock Exchange (PSX).
    Use this whenever a user provides a company name and you need the exact official symbol.
    
    Args:
        query: The company name or partial ticker (e.g., "Hub Power", "Lucky Cement", "MEBL").
        
    Returns:
        A dictionary containing the search status and up to 5 best matches.
    """
    return _search_ticker(query)

@mcp.tool()
def get_historical_prices(query: str, start_date: str, end_date: str) -> dict:
    """
    Retrieves historical OHLCV (Open, High, Low, Close, Volume) market data for a given company on the Pakistan Stock Exchange.
    Returns the data sorted chronologically (oldest to newest).
    
    Args:
        query: The name or ticker of the company (e.g., "Hub Power", "HUBC", "Lucky Cement").
        start_date: The beginning of the date range in YYYY-MM-DD format (e.g., "2023-01-01").
        end_date: The end of the date range in YYYY-MM-DD format (e.g., "2023-12-31").
        
    Returns:
        A dictionary containing the historical data points or an error message.
    """
    return _get_historical_prices(query, start_date, end_date)

@mcp.tool()
def list_tickers() -> dict:
    """
    Retrieves a complete list of all official company tickers listed on the Pakistan Stock Exchange (PSX).
    Use this when you need to audit the available market, count the total listed companies, 
    or check if a specific sector/company exists in the broader market.
    
    Returns:
        A dictionary containing the total count and the full list of ticker/company pairs.
    """
    return _list_tickers()

@mcp.tool()
def get_index_constituents(index_name: str) -> dict:
    """
    Retrieves the constituents (listed companies) of a named index on the Pakistan Stock Exchange (PSX).
    Use this to see which companies make up major market indices.
    
    Args:
        index_name: The name of the index to fetch (e.g., "KSE100", "KMI30", "ALLSHR").
        
    Returns:
        A dictionary containing the index name, total count of constituents, and the list of companies.
    """
    return _get_index_constituents(index_name)
@mcp.tool()

def get_sector_summary() -> dict:
    """
    Retrieves the aggregate daily performance of all market sectors on the Pakistan Stock Exchange (PSX).
    Use this to get a macro-level view of the market, identify top-performing or underperforming sectors, 
    and analyze sector-wide trading volumes.
    
    Returns:
        A dictionary containing the total count of sectors and a list of their aggregated market data.
    """
    return _get_sector_summary()

#=========================================================
#                EQUITY AND VALUATION TOOLS
#=========================================================

@mcp.tool()
def get_etf_performance(query: str, start_date: str, end_date: str) -> dict:
    """
    Retrieves historical performance records specifically for Exchange Traded Funds (ETFs) 
    listed on the Pakistan Stock Exchange (PSX).
    
    Args:
        query: The name or specific ticker of the ETF (e.g., "Meezan ETF", "MZNPETF", "NITGETF").
        start_date: Start of the window in YYYY-MM-DD format (e.g., "2026-06-01").
        end_date: End of the window in YYYY-MM-DD format (e.g., "2026-06-20").
        
    Returns:
        A dictionary containing clean historical ETF metrics sorted oldest to newest.
    """
    return _get_etf_data(query, start_date, end_date)

@mcp.tool()
def value_stock_ddm(dividend: float, required_return: float, growth_rate: float, ticker: str = None) -> dict:
    """
    Calculates the intrinsic fair value of a dividend-paying stock using the Gordon Growth Model 
    (Dividend Discount Model).
    
    Args:
        dividend: The expected dividend per share for the next year (D1).
        required_return: The investor's required rate of return as a decimal (e.g., enter 0.15 for 15%).
        growth_rate: The expected perpetual growth rate of the company's dividend as a decimal (e.g., enter 0.05 for 5%).
        ticker: (Optional) The stock symbol, used purely for labeling the output.
        
    Returns:
        A dictionary containing the calculated fair value price of the stock.
    """
    return _value_stock_ddm(dividend, required_return, growth_rate, ticker)

@mcp.tool()
def value_stock_two_stage_ddm(
    current_dividend: float, 
    required_return: float, 
    high_growth_rate: float, 
    high_growth_years: int, 
    stable_growth_rate: float, 
    ticker: str = None
) -> dict:
    """
    Calculates the intrinsic fair value of a stock using the Two-Stage Dividend Discount Model.
    Use this for companies expected to grow rapidly for a set number of years before settling into a stable rate.
    
    Args:
        current_dividend: The most recent annual dividend paid (D0).
        required_return: The investor's required rate of return as a decimal (e.g., enter 0.15 for 15%).
        high_growth_rate: The expected growth rate during the initial high-growth phase as a decimal.
        high_growth_years: The number of years the high-growth phase is expected to last.
        stable_growth_rate: The perpetual growth rate expected after the high-growth phase as a decimal.
        ticker: (Optional) The stock symbol, used purely for labeling the output.
        
    Returns:
        A dictionary containing the calculated fair value price of the stock based on the two-stage model.
    """
    return _value_stock_two_stage_ddm(
        current_dividend, 
        required_return, 
        high_growth_rate, 
        high_growth_years, 
        stable_growth_rate, 
        ticker
    )

@mcp.tool()
def value_stock_pe(eps: float, target_pe: float, ticker: str = None) -> dict:
    """
    Calculates the implied fair value of a stock using the Relative Valuation (P/E Multiple) model.
    Use this when comparing a company against its sector or peers.
    
    Args:
        eps: The company's trailing or forward Earnings Per Share (must be positive).
        target_pe: The target or industry-average Price-to-Earnings ratio to multiply by.
        ticker: (Optional) The stock symbol, used purely for labeling the output.
        
    Returns:
        A dictionary containing the calculated fair value price of the stock based on peer multiples.
    """
    return _value_stock_pe(eps, target_pe, ticker)

@mcp.tool()
def value_stock_dcf(
    projected_fcfs: list[float], 
    wacc: float, 
    terminal_growth_rate: float, 
    net_debt: float = 0.0, 
    shares_outstanding: float = None, 
    ticker: str = None
) -> dict:
    """
    Calculates the intrinsic fair value of a company using a multi-year Discounted Cash Flow (DCF) model.
    Use this when you have specific annual Free Cash Flow projections.
    
    Args:
        projected_fcfs: A list of expected future cash flows (e.g., [120.0, 140.0, 165.0, 190.0]).
        wacc: The Weighted Average Cost of Capital as a decimal (e.g., 0.14 for 14%).
        terminal_growth_rate: The perpetual stable growth rate as a decimal (e.g., 0.04 for 4%).
        net_debt: (Optional) Total Debt minus Total Cash. Subtracts from Enterprise Value to find Equity Value.
        shares_outstanding: (Optional) Total outstanding shares to calculate fair value per share.
        ticker: (Optional) The stock symbol, used purely for labeling the output.
        
    Returns:
        A dictionary showcasing Enterprise Value, Equity Value, and Intrinsic Value per share.
    """
    return _value_stock_dcf(
        projected_fcfs, 
        wacc, 
        terminal_growth_rate, 
        net_debt, 
        shares_outstanding, 
        ticker
    )

@mcp.tool()
def calculate_dividend_yield(annual_dividend: float, current_price: float, ticker: str = None) -> dict:
    """
    Calculates the current dividend yield of a stock based on its payout and market price.
    Use this to evaluate the income-generation potential of a dividend-paying company.
    
    Args:
        annual_dividend: The total cash dividend paid out per share over a year (Trailing or Forward).
        current_price: The current trading market price of the stock.
        ticker: (Optional) The stock symbol, used purely for labeling the output.
        
    Returns:
        A dictionary containing the dividend yield formatted as both a decimal and a percentage string.
    """
    return _calculate_dividend_yield(annual_dividend, current_price, ticker)

@mcp.tool()
def compare_peer_valuation(peers_data: list[dict]) -> dict:
    """
    Compares cross-sectional valuation multiples and dividend profiles across a list of peer companies.
    Use this to execute relative analysis and identify industry laggards or leaders.
    
    Args:
        peers_data: A list of dictionaries for each peer company. Each dictionary must follow this structure:
                    {"ticker": "HUBC", "pe": 6.2, "pb": 1.4, "dividend_yield": 0.115, "market_cap": 145000.0}
                    Note: Express dividend_yield as a decimal (e.g., 0.115 for 11.5%).
                    
    Returns:
        A dictionary showcasing computed peer group averages alongside the comparative breakdown for each ticker.
    """
    return _compare_peer_valuation(peers_data)

@mcp.tool()
def get_etf_inav(ticker: str) -> dict:
    """Fetch the live Indicative Net Asset Value (iNAV) and market quote for a given ETF.

    Args:
        ticker (str): The official ETF symbol on the PSX (e.g., 'MZNPETF', 'UBLPETF', 'MIIETF', 'NITGETF').

    Returns:
        dict: A dictionary containing the ETF pricing data, status, and the data source 
              (e.g., {"status": "success", "source": "psxdata_live_quote", "data": {...}}).
    """
    return _get_etf_inav(ticker)

@mcp.tool()
def calculate_etf_premium_discount(market_price: float, inav: float) -> dict:
    """Calculate the premium or discount of an ETF's market price relative to its iNAV.
    
    Args:
        market_price (float): The current live trading price of the ETF.
        inav (float): The current Indicative Net Asset Value (iNAV) of the ETF.
        
    Returns:
        dict: A dictionary containing the absolute difference, the percentage deviation, 
              and a status label indicating if it is trading at a 'Premium', 'Discount', or 'Par'.
    """
    return _calculate_etf_premium_discount(market_price, inav)

@mcp.tool()
def calculate_etf_tracking_difference(etf_return: float, benchmark_return: float) -> dict:
    """Calculate the tracking difference between an ETF and its underlying benchmark index.
    
    Args:
        etf_return (float): The total return of the ETF over a given period.
        benchmark_return (float): The total return of the benchmark index over the exact same period.
        
    Returns:
        dict: A dictionary containing the calculated tracking difference and a status label 
              indicating 'Outperformance', 'Underperformance', or 'Exact Match'.
    """
    return _calculate_etf_tracking_difference(etf_return, benchmark_return)


#=========================================================
#                     ADVISOR TOOLS
#=========================================================

@mcp.tool()
def analyze_holding(
    ticker: str, 
    market_price: float, 
    fundamental_value: float, 
    inflation_rate: float, 
    nominal_yield: float
) -> dict:
    """Composes a synthesized advisory report by comparing price, value, and inflation.
    
    Args:
        ticker (str): The official symbol of the equity or ETF.
        market_price (float): The current live trading price from the market.
        fundamental_value (float): The fair value (use iNAV for ETFs, or Intrinsic Value for Equities).
        inflation_rate (float): The current macroeconomic inflation rate (e.g., 12.5 for 12.5%).
        nominal_yield (float): The expected dividend or distribution yield percentage.
        
    Returns:
        dict: A synthesized report detailing upside potential, inflation-adjusted (real) yield, 
              and an automated advisor conviction signal.
    """
    return _analyze_holding(ticker, market_price, fundamental_value, inflation_rate, nominal_yield)

@mcp.tool()
def portfolio_health_check(holdings: list[dict], cash_flows: list[dict] = None) -> dict:
    """Evaluates overall portfolio health by analyzing asset allocation, concentration risk, and XIRR.
    
    Args:
        holdings (list[dict]): A list of dictionaries representing current assets. 
                               Format: [{"ticker": "ENGRO", "value": 50000.0}, {"ticker": "HUBC", "value": 15000.0}]
        cash_flows (list[dict], optional): A list of dictionaries representing portfolio deposits/withdrawals over time.
                                           Negative amounts for investments, positive amounts for current total value/withdrawals.
                                           Format: [{"date": "2024-01-01", "amount": -65000.0}, {"date": "2025-01-01", "amount": 75000.0}]
        
    Returns:
        dict: A detailed diagnostic report including allocation weights, concentration risk flags, XIRR, 
              and a synthesized health signal.
    """
    return _portfolio_health_check(holdings, cash_flows)