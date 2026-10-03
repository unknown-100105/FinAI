from investment_catalog import (
    RATE_END,
    RATE_START,
    SMALL_SAVINGS,
    bond_plan,
    fd_plan,
    list_mutual_fund_categories,
    sip_plan,
    small_savings_projection,
)


def test_current_small_savings_period_and_rates():
    assert RATE_START == "2026-10-01"
    assert RATE_END == "2026-12-31"

    by_id = {item.product_id: item for item in SMALL_SAVINGS}
    assert by_id["ppf"].rate_percent == 7.1
    assert by_id["nsc"].rate_percent == 7.7
    assert by_id["scss"].rate_percent == 8.2
    assert by_id["mis"].rate_percent == 7.4


def test_sip_plan_returns_deterministic_projection():
    result = sip_plan(
        monthly_investment=5000,
        annual_return_percent=12,
        years=10,
        annual_step_up_percent=10,
        annual_inflation_percent=6,
        target_corpus=10_000_000,
    )

    assert result["total_invested"] > 0
    assert result["projected_value"] > result["total_invested"]
    assert result["projected_gain"] > 0
    assert result["inflation_adjusted_value_today"] < result["projected_value"]
    assert result["required_starting_monthly_investment"] > 0


def test_fd_plan():
    result = fd_plan(
        principal=100_000,
        annual_rate_percent=7,
        years=5,
        compounding_per_year=4,
    )

    assert result["maturity_value"] > 100_000
    assert result["interest_earned"] > 0


def test_bond_price_moves_below_face_when_yield_exceeds_coupon():
    result = bond_plan(
        face_value=100_000,
        coupon_rate_percent=7,
        yield_percent=8,
        years_to_maturity=5,
        coupon_frequency=2,
    )

    assert result["estimated_clean_price"] < 100_000
    assert result["premium_discount_percent"] < 0


def test_small_savings_projection_exposes_source_metadata():
    result = small_savings_projection("ppf", 100_000)
    assert result["product"]["source"] == "Department of Economic Affairs, Ministry of Finance"
    assert result["product"]["source_url"].startswith("https://")
    assert result["illustrative_value"] > result["principal"]


def test_mutual_fund_structure_has_current_groups():
    categories = list_mutual_fund_categories()
    names = {item["name"] for item in categories}
    assert {"Equity", "Debt", "Hybrid", "Life Cycle", "Other"} <= names
