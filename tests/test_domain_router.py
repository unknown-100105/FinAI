from router.domain_router import (
    FinAIDomainRouter,
    DOMAIN_BANKING,
    DOMAIN_CALCULATION,
    DOMAIN_FINANCIAL_KNOWLEDGE,
    DOMAIN_MARKET_DATA,
    DOMAIN_PRODUCT_COMPARISON,
    DOMAIN_REGULATORY_KNOWLEDGE,
    DOMAIN_SCHEME_KNOWLEDGE,
    DOMAIN_SUPPORT,
    DOMAIN_UNKNOWN,
)


def test_known_emi_intent_maps_to_calculation():
    router = FinAIDomainRouter()

    result = router.route(
        "Calculate my EMI",
        classified_intent="EMI_QUERY",
    )

    assert result["domain"] == DOMAIN_CALCULATION
    assert result["source"] == "known_intent"


def test_card_lost_maps_to_banking():
    router = FinAIDomainRouter()

    result = router.route(
        "My card is lost",
        classified_intent="CARD_LOST",
    )

    assert result["domain"] == DOMAIN_BANKING


def test_kcy_document_question_maps_to_financial_knowledge():
    router = FinAIDomainRouter()

    result = router.route(
        "What documents are required for KYC?",
        classified_intent="KYC_DOCUMENTS",
    )

    assert result["domain"] == DOMAIN_FINANCIAL_KNOWLEDGE


def test_stock_chart_query_maps_to_market_data():
    router = FinAIDomainRouter()

    result = router.route(
        "Show me the NIFTY chart for the last one year"
    )

    assert result["domain"] == DOMAIN_MARKET_DATA


def test_forex_query_maps_to_market_data():
    router = FinAIDomainRouter()

    result = router.route(
        "What is USD INR today?"
    )

    assert result["domain"] == DOMAIN_MARKET_DATA


def test_crypto_query_maps_to_market_data():
    router = FinAIDomainRouter()

    result = router.route(
        "Show Bitcoin historical price data"
    )

    assert result["domain"] == DOMAIN_MARKET_DATA


def test_regulation_query_maps_to_regulatory():
    router = FinAIDomainRouter()

    result = router.route(
        "What are the current SEBI regulations for investment advisers?"
    )

    assert result["domain"] == DOMAIN_REGULATORY_KNOWLEDGE


def test_post_office_query_maps_to_scheme():
    router = FinAIDomainRouter()

    result = router.route(
        "Explain Post Office savings schemes"
    )

    assert result["domain"] == DOMAIN_SCHEME_KNOWLEDGE


def test_credit_card_query_maps_to_product_comparison():
    router = FinAIDomainRouter()

    result = router.route(
        "What credit cards have airport lounge benefits?"
    )

    assert result["domain"] == DOMAIN_PRODUCT_COMPARISON



def test_product_query_overrides_conflicting_known_banking_intent():
    router = FinAIDomainRouter()

    result = router.route(
        "What credit cards have airport lounge benefits?",
        classified_intent="ACCOUNT_BALANCE",
    )

    assert result["domain"] == DOMAIN_PRODUCT_COMPARISON
    assert result["source"] == "deterministic_domain_rule"


def test_credit_card_payment_failure_stays_banking():
    router = FinAIDomainRouter()

    result = router.route(
        "My credit card payment failed",
        classified_intent="CARD_PAYMENT_FAILED",
    )

    assert result["domain"] == DOMAIN_BANKING

def test_investment_education_maps_to_financial_knowledge():
    router = FinAIDomainRouter()

    result = router.route(
        "What is a mutual fund and how does investing work?"
    )

    assert result["domain"] == DOMAIN_FINANCIAL_KNOWLEDGE


def test_what_if_calculation_maps_to_calculation():
    router = FinAIDomainRouter()

    result = router.route(
        "What if I increase my SIP from 5000 to 8000?"
    )

    assert result["domain"] == DOMAIN_CALCULATION


def test_support_maps_to_support():
    router = FinAIDomainRouter()

    result = router.route(
        "I need help with my account",
        classified_intent="SUPPORT_REQUEST",
    )

    assert result["domain"] == DOMAIN_SUPPORT


def test_unknown_stays_unknown():
    router = FinAIDomainRouter()

    result = router.route(
        "Tell me about cricket"
    )

    assert result["domain"] == DOMAIN_UNKNOWN


def test_empty_input_stays_unknown():
    router = FinAIDomainRouter()

    result = router.route("")

    assert result["domain"] == DOMAIN_UNKNOWN
