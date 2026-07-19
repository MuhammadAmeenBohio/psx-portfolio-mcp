import math


def future_value(
        principal: float,
        annual_rate: float,
        compounding: str,
        years: float
) -> dict:
    """
    Calculates the future value based on string-based compounding frequencies.
    """
    compounding_map = {
        "annually": 1,
        "semi_annually": 2,
        "quarterly": 4,  # Fixed typo here
        "monthly": 12,
        "daily": 365,
    }

    compounds_per_year = compounding_map.get(compounding, 1)
    
    annual_rate_p = annual_rate / 100

    fv = principal * (1 + annual_rate_p / compounds_per_year) ** (compounds_per_year * years)

    return {"future_value": fv}


def present_value(
        future_value: float,
        annual_rate: float,
        compounding: str,
        years: float
) -> dict:
    """
    Calculate the present value based on string-based frequencies.
    """
    compounding_map = {
        "annually": 1,
        "semi_annually": 2,
        "quarterly": 4,
        "monthly": 12,
        "daily": 365,
    }

    compounds_per_year = compounding_map.get(compounding, 1)

    annual_rate_p = annual_rate / 100

    denominator = (1 + annual_rate_p / compounds_per_year) ** (compounds_per_year * years)

    pv = future_value / denominator
    return {"present_value": pv}

def annuity_fv(
        payment: float,
        annual_rate: float,
        compounding: str,
        years: float,
        payment_timing: str = "end"
) -> dict:
    """
    Calculates the future value of an annuity (recurring payments).
    """
    compounding_map = {
        "annually": 1,
        "semi_annually": 2,
        "quarterly": 4,
        "monthly": 12,
        "daily": 365,
    }

    compounds_per_year = compounding_map.get(compounding, 1)
    
    annual_rate_p = annual_rate / 100
    rate_per_period = annual_rate_p / compounds_per_year
    total_periods = compounds_per_year * years

    if rate_per_period == 0:
        fv = payment * total_periods
    else:
        fv = payment * (((1 + rate_per_period) ** total_periods - 1) / rate_per_period)
        
        if payment_timing.lower() == "begin":
            fv = fv * (1 + rate_per_period)

    return {"future_value_annuity": fv}

def annuity_pv(
    payment: float,
    annual_rate: float,
    compounding: str,
    years: float,
    payment_timing: str = "end"
) -> dict:
    """
    Calculates the present value of an annuity (recurring payments).
    """
    compounding_map = {
        "annually": 1,
        "semi_annually": 2,
        "quarterly": 4,
        "monthly": 12,
        "daily": 365,
    }

    compounds_per_year = compounding_map.get(compounding, 1)

    annual_rate_p = annual_rate / 100
    rate_per_period = annual_rate_p / compounds_per_year
    total_periods = compounds_per_year * years

    if rate_per_period == 0:
        pv = payment * total_periods
    else:
        pv = payment * ((1 - (1 + rate_per_period) ** -total_periods) / rate_per_period)
        
        if payment_timing.lower() == "begin":
            pv = pv * (1 + rate_per_period)

    return {"present_value_annuity": pv} 

def perpetuity_pv(
        payment: float,
        annual_rate: float,
        compounding: str,
        growth_rate: float = 0.0
) -> dict:
    """
    Calculates the present value of an infinite payment stream (perpetuity) with optional growth.
    """
    compounding_map = {
        "annually": 1,
        "semi_annually": 2,
        "quarterly": 4,
        "monthly": 12,
        "daily": 365,
    }

    compounds_per_year = compounding_map.get(compounding, 1)
    
    annual_rate_p = annual_rate / 100
    growth_rate_p = growth_rate / 100

    rate_per_period = annual_rate_p / compounds_per_year
    growth_per_period = growth_rate_p / compounds_per_year

    if rate_per_period <= growth_per_period:
        raise ValueError("The interest rate must be strictly greater than the growth rate for a perpetuity.")

    pv = payment / (rate_per_period - growth_per_period)

    return {"present_value_perpetuity": pv}

def rule_of_72(annual_rate: float) -> dict:
    """
    Calculates the estimated (Rule of 72) and exact time required for an investment to double.
    """

    if annual_rate <= 0:
        raise ValueError("Annual rate must be greater than 0 to calculate doubling time.")

    rule_of_72_years = 72 / annual_rate

    annual_rate_p = annual_rate / 100
    exact_years = math.log(2) / math.log(1 + annual_rate_p)

    return {
        "rule_of_72_estimate_years": rule_of_72_years,
        "exact_doubling_years": exact_years,
        "difference_years": abs(rule_of_72_years - exact_years)
    }

def effective_rate(nominal_rate: float, compounding: str) -> dict:
    """
    Calculates the Effective Annual Rate (EAR) from a nominal rate and compounding frequency.
    """
    compounding_map = {
        "annually": 1,
        "semi_annually": 2,
        "quarterly": 4,
        "monthly": 12,
        "daily": 365,
    }

    compounds_per_year = compounding_map.get(compounding, 1)
    
    nominal_rate_p = nominal_rate / 100

    ear_decimal = (1 + nominal_rate_p / compounds_per_year) ** compounds_per_year - 1

    ear_percentage = ear_decimal * 100

    return {"effective_rate": ear_percentage}

def savings_needed(
        target_amount: float,
        years: float,
        annual_rate: float,
        current_savings: float,
        compounding: str
) -> dict:
    """
    Calculates the regular contribution needed to reach a target financial goal.
    """
    compounding_map = {
        "annually": 1,
        "semi_annually": 2,
        "quarterly": 4,
        "monthly": 12,
        "daily": 365,
    }

    compounds_per_year = compounding_map.get(compounding, 12)
    
    annual_rate_p = annual_rate / 100
    rate_per_period = annual_rate_p / compounds_per_year
    total_periods = compounds_per_year * years

    if rate_per_period == 0:
        payment = (target_amount - current_savings) / total_periods
    else:
        fv_of_current_savings = current_savings * ((1 + rate_per_period) ** total_periods)
        
        remaining_goal = target_amount - fv_of_current_savings
        
        payment = (remaining_goal * rate_per_period) / (((1 + rate_per_period) ** total_periods) - 1)

    return {"payment_needed": payment}