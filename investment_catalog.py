"""Structured investment product data and deterministic planning calculators.

Current small-savings rates are the Government of India Department of Economic Affairs
Q3 FY 2026-27 rates, effective 2026-10-01 through 2026-12-31.
Source: https://dea.gov.in/budget-division/475
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from math import isfinite
from typing import Any, Dict, List, Optional


RATE_START = "2026-10-01"
RATE_END = "2026-12-31"
RATE_SOURCE = "Department of Economic Affairs, Ministry of Finance"
RATE_SOURCE_URL = "https://dea.gov.in/budget-division/475"


@dataclass(frozen=True)
class InvestmentProduct:
    product_id: str
    name: str
    category: str
    rate_percent: Optional[float]
    tenure: str
    payout: str
    eligibility: str
    liquidity: str
    tax_note: str
    risk_note: str
    description: str
    source: str
    source_url: str
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None


def _p(
    product_id: str,
    name: str,
    rate: Optional[float],
    tenure: str,
    payout: str,
    eligibility: str,
    liquidity: str,
    description: str,
) -> InvestmentProduct:
    return InvestmentProduct(
        product_id=product_id,
        name=name,
        category="Post Office",
        rate_percent=rate,
        tenure=tenure,
        payout=payout,
        eligibility=eligibility,
        liquidity=liquidity,
        tax_note="Tax treatment should be verified under current income-tax rules.",
        risk_note="Scheme terms, eligibility and withdrawal conditions apply.",
        description=description,
        source=RATE_SOURCE,
        source_url=RATE_SOURCE_URL,
        effective_from=RATE_START,
        effective_to=RATE_END,
    )


SMALL_SAVINGS = (
    _p("post_savings", "Post Office Savings Account", 4.0, "No fixed tenure",
       "Interest under scheme rules", "Eligible Post Office customers",
       "Withdrawals subject to account rules", "Basic Post Office savings account."),
    _p("post_td_1y", "Post Office Time Deposit — 1 Year", 6.9, "1 year",
       "Interest under scheme rules", "Eligible Post Office customers",
       "Premature withdrawal subject to scheme rules", "One-year fixed-tenure deposit."),
    _p("post_td_2y", "Post Office Time Deposit — 2 Years", 7.0, "2 years",
       "Interest under scheme rules", "Eligible Post Office customers",
       "Premature withdrawal subject to scheme rules", "Two-year fixed-tenure deposit."),
    _p("post_td_3y", "Post Office Time Deposit — 3 Years", 7.1, "3 years",
       "Interest under scheme rules", "Eligible Post Office customers",
       "Premature withdrawal subject to scheme rules", "Three-year fixed-tenure deposit."),
    _p("post_td_5y", "Post Office Time Deposit — 5 Years", 7.5, "5 years",
       "Interest under scheme rules", "Eligible Post Office customers",
       "Premature withdrawal subject to scheme rules", "Five-year fixed-tenure deposit."),
    _p("post_rd_5y", "Post Office Recurring Deposit — 5 Years", 6.7, "5 years",
       "Periodic contributions + interest", "Eligible Post Office customers",
       "Subject to scheme rules", "Recurring-deposit small-savings product."),
    _p("scss", "Senior Citizens' Savings Scheme (SCSS)", 8.2, "5 years",
       "Interest on the scheme schedule", "Eligible senior citizens under current rules",
       "Premature closure subject to scheme rules", "Small-savings product for eligible senior citizens."),
    _p("mis", "Monthly Income Account Scheme (MIS)", 7.4, "5 years",
       "Monthly interest under scheme rules", "Eligible Post Office customers",
       "Premature closure subject to scheme rules", "Small-savings account designed around periodic income."),
    _p("nsc", "National Savings Certificate (NSC)", 7.7, "5 years",
       "Interest accrues under scheme rules", "Eligible Post Office customers",
       "Early encashment limited by scheme rules", "Five-year small-savings certificate."),
    _p("ppf", "Public Provident Fund (PPF)", 7.1, "15 years",
       "Interest credited under PPF rules", "Eligible individuals under current PPF rules",
       "Long lock-in with conditional access", "Long-term small-savings product."),
    _p("kvp", "Kisan Vikas Patra (KVP)", 7.5, "115 months",
       "Maturity under scheme rules", "Eligible Post Office customers",
       "Premature encashment subject to scheme rules", "Small-savings certificate with current 115-month maturity."),
    _p("sukanya", "Sukanya Samriddhi Account", 8.2, "Scheme-specific long-term tenure",
       "Interest credited under scheme rules", "Eligible accounts under current rules",
       "Withdrawals subject to scheme conditions", "Small-savings account for eligible girl-child accounts."),
)


@dataclass(frozen=True)
class MutualFundCategory:
    category_id: str
    name: str
    group: str
    description: str
    what_to_check: tuple[str, ...]


MUTUAL_FUND_CATEGORIES = (
    MutualFundCategory(
        "equity", "Equity", "Equity Scheme",
        "Schemes predominantly investing in equity and equity-related instruments.",
        ("asset allocation", "expense ratio", "riskometer", "concentration", "scheme disclosures"),
    ),
    MutualFundCategory(
        "debt", "Debt", "Debt Scheme",
        "Schemes predominantly investing in debt and debt-related instruments.",
        ("credit quality", "duration", "yield", "interest-rate sensitivity", "liquidity"),
    ),
    MutualFundCategory(
        "hybrid", "Hybrid", "Hybrid Scheme",
        "Schemes investing across permitted combinations of asset classes.",
        ("asset allocation", "rebalancing", "equity exposure", "debt exposure", "risk disclosures"),
    ),
    MutualFundCategory(
        "life_cycle", "Life Cycle", "Life Cycle Fund",
        "Funds structured around a life-cycle or target-horizon framework.",
        ("target horizon", "glide path", "asset allocation", "fees", "risk disclosures"),
    ),
    MutualFundCategory(
        "other", "Other", "Other Schemes",
        "Includes Fund of Funds and passive schemes such as index funds/ETFs.",
        ("underlying assets", "tracking difference", "fees", "liquidity", "portfolio disclosures"),
    ),
)


def product_payload(product: InvestmentProduct) -> Dict[str, Any]:
    return asdict(product)


def list_products(category: Optional[str] = None) -> List[Dict[str, Any]]:
    products = SMALL_SAVINGS
    if category:
        normalized = category.strip().lower()
        products = tuple(item for item in products if item.category.lower() == normalized)
    return [product_payload(item) for item in products]


def list_mutual_fund_categories() -> List[Dict[str, Any]]:
    return [asdict(item) for item in MUTUAL_FUND_CATEGORIES]


def _positive(value: float, name: str) -> float:
    value = float(value)
    if not isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be greater than zero.")
    return value


def sip_plan(
    monthly_investment: float,
    annual_return_percent: float,
    years: float,
    annual_step_up_percent: float = 0.0,
    annual_inflation_percent: float = 0.0,
    target_corpus: Optional[float] = None,
) -> Dict[str, Any]:
    monthly = _positive(monthly_investment, "monthly_investment")
    years_value = _positive(years, "years")
    annual_return = float(annual_return_percent) / 100.0
    inflation = float(annual_inflation_percent) / 100.0
    step_up = float(annual_step_up_percent) / 100.0

    if annual_return <= -1 or inflation <= -1 or step_up < 0:
        raise ValueError("Return, inflation or step-up assumptions are invalid.")

    months = max(1, int(round(years_value * 12)))
    monthly_rate = (1 + annual_return) ** (1 / 12) - 1
    balance = 0.0
    invested = 0.0
    contribution = monthly

    for month in range(1, months + 1):
        balance = balance * (1 + monthly_rate) + contribution
        invested += contribution
        if month % 12 == 0:
            contribution *= 1 + step_up

    inflation_adjusted = balance / ((1 + inflation) ** years_value)

    result = {
        "monthly_investment": monthly,
        "annual_return_percent": annual_return_percent,
        "years": years_value,
        "annual_step_up_percent": annual_step_up_percent,
        "annual_inflation_percent": annual_inflation_percent,
        "total_invested": invested,
        "projected_value": balance,
        "projected_gain": balance - invested,
        "inflation_adjusted_value_today": inflation_adjusted,
        "method": "Monthly contribution simulation; return is an assumption, not a guarantee.",
    }

    if target_corpus is not None:
        target = _positive(target_corpus, "target_corpus")

        def project(start: float) -> float:
            value = 0.0
            contribution_inner = start
            for month_inner in range(1, months + 1):
                value = value * (1 + monthly_rate) + contribution_inner
                if month_inner % 12 == 0:
                    contribution_inner *= 1 + step_up
            return value

        low, high = 0.0, target / max(1, months)
        while project(high) < target and high < 1e9:
            high *= 2
        for _ in range(70):
            mid = (low + high) / 2
            if project(mid) >= target:
                high = mid
            else:
                low = mid

        result["target_corpus"] = target
        result["required_starting_monthly_investment"] = high

    return result


def fd_plan(
    principal: float,
    annual_rate_percent: float,
    years: float,
    compounding_per_year: int = 4,
) -> Dict[str, Any]:
    principal = _positive(principal, "principal")
    years = _positive(years, "years")
    rate = float(annual_rate_percent) / 100
    frequency = int(compounding_per_year)
    if rate < 0 or frequency <= 0:
        raise ValueError("FD assumptions are invalid.")

    maturity = principal * (1 + rate / frequency) ** (frequency * years)
    return {
        "principal": principal,
        "annual_rate_percent": annual_rate_percent,
        "years": years,
        "compounding_per_year": frequency,
        "maturity_value": maturity,
        "interest_earned": maturity - principal,
        "method": "Illustrative compound-interest projection; issuer rules may differ.",
    }


def bond_plan(
    face_value: float,
    coupon_rate_percent: float,
    yield_percent: float,
    years_to_maturity: float,
    coupon_frequency: int = 2,
) -> Dict[str, Any]:
    face = _positive(face_value, "face_value")
    years = _positive(years_to_maturity, "years_to_maturity")
    frequency = int(coupon_frequency)
    if frequency <= 0:
        raise ValueError("coupon_frequency must be positive.")

    coupon = face * (float(coupon_rate_percent) / 100) / frequency
    periods = max(1, int(round(years * frequency)))
    period_yield = float(yield_percent) / 100 / frequency
    if period_yield <= -1:
        raise ValueError("yield_percent is invalid.")

    price = sum(coupon / ((1 + period_yield) ** t) for t in range(1, periods + 1))
    price += face / ((1 + period_yield) ** periods)

    return {
        "face_value": face,
        "coupon_rate_percent": coupon_rate_percent,
        "yield_percent": yield_percent,
        "years_to_maturity": years,
        "coupon_frequency": frequency,
        "annual_coupon": face * float(coupon_rate_percent) / 100,
        "estimated_clean_price": price,
        "premium_discount_percent": ((price / face) - 1) * 100,
        "method": "Present-value model using coupon, yield and remaining periods.",
    }


def small_savings_projection(product_id: str, principal: float, years: Optional[float] = None) -> Dict[str, Any]:
    product = next((item for item in SMALL_SAVINGS if item.product_id == product_id), None)
    if product is None or product.rate_percent is None:
        raise ValueError(f"Unknown small-savings product: {product_id}")

    principal = _positive(principal, "principal")
    rate = product.rate_percent / 100

    if product_id == "scss":
        return {
            "product": product_payload(product),
            "principal": principal,
            "annual_interest": principal * rate,
            "quarterly_interest": principal * rate / 4,
            "illustrative_value": principal,
            "method": "Quarterly-income illustration.",
        }

    if product_id == "mis":
        return {
            "product": product_payload(product),
            "principal": principal,
            "annual_interest": principal * rate,
            "monthly_interest": principal * rate / 12,
            "illustrative_value": principal,
            "method": "Monthly-income illustration.",
        }

    if product_id == "kvp":
        return {
            "product": product_payload(product),
            "principal": principal,
            "maturity_months": 115,
            "illustrative_value": principal * 2,
            "method": "Current notified KVP maturity convention.",
        }

    default_years = {
        "post_td_1y": 1.0, "post_td_2y": 2.0, "post_td_3y": 3.0,
        "post_td_5y": 5.0, "nsc": 5.0, "ppf": 15.0,
    }.get(product_id, years or 1.0)

    projection_years = _positive(default_years, "years")
    value = principal * (1 + rate) ** projection_years

    return {
        "product": product_payload(product),
        "principal": principal,
        "years": projection_years,
        "illustrative_value": value,
        "illustrative_interest": value - principal,
        "method": "Illustrative annual-compounding projection; actual scheme crediting rules apply.",
    }


def catalog_metadata() -> Dict[str, Any]:
    return {
        "rate_period": f"{RATE_START} to {RATE_END}",
        "rate_source": RATE_SOURCE,
        "rate_source_url": RATE_SOURCE_URL,
        "today": date.today().isoformat(),
        "note": "Refresh official notifications before a real transaction.",
    }
