from typing import Dict, Optional


DOMAIN_BANKING = "BANKING"
DOMAIN_MARKET_DATA = "MARKET_DATA"
DOMAIN_FINANCIAL_KNOWLEDGE = "FINANCIAL_KNOWLEDGE"
DOMAIN_REGULATORY_KNOWLEDGE = "REGULATORY_KNOWLEDGE"
DOMAIN_SCHEME_KNOWLEDGE = "SCHEME_KNOWLEDGE"
DOMAIN_PRODUCT_COMPARISON = "PRODUCT_COMPARISON"
DOMAIN_CALCULATION = "CALCULATION"
DOMAIN_SUPPORT = "SUPPORT"
DOMAIN_UNKNOWN = "UNKNOWN"


# Existing trained intents are mapped into broader execution domains.
KNOWN_INTENT_DOMAINS = {
    "ACCOUNT_BALANCE": DOMAIN_BANKING,
    "ACCOUNT_COMPROMISED": DOMAIN_BANKING,
    "ACCOUNT_LOCKED": DOMAIN_BANKING,
    "PASSWORD_RESET": DOMAIN_BANKING,
    "PROFILE_UPDATE": DOMAIN_BANKING,
    "CARD_ACTIVATION": DOMAIN_BANKING,
    "CARD_BLOCK": DOMAIN_BANKING,
    "CARD_LOST": DOMAIN_BANKING,
    "CARD_STOLEN": DOMAIN_BANKING,
    "CARD_UNBLOCK": DOMAIN_BANKING,
    "CARD_PAYMENT_FAILED": DOMAIN_BANKING,
    "PIN_FAILED": DOMAIN_BANKING,
    "PAYMENT_FAILED": DOMAIN_BANKING,
    "PAYMENT_PENDING": DOMAIN_BANKING,
    "PAYMENT_SUCCESS": DOMAIN_BANKING,
    "PAYMENT_CANCEL_REQUEST": DOMAIN_BANKING,
    "PAYMENT_LIMIT": DOMAIN_BANKING,
    "UPI_COLLECT_REQUEST": DOMAIN_BANKING,
    "UPI_ID_ISSUE": DOMAIN_BANKING,
    "UPI_PAYMENT_FAILED": DOMAIN_BANKING,
    "UPI_PENDING": DOMAIN_BANKING,
    "BANK_TRANSFER_FAILED": DOMAIN_BANKING,
    "BANK_TRANSFER_PENDING": DOMAIN_BANKING,
    "BANK_TRANSFER_STATUS": DOMAIN_BANKING,
    "BENEFICIARY_ISSUE": DOMAIN_BANKING,
    "CASH_WITHDRAWAL_FAILED": DOMAIN_BANKING,
    "CASH_WITHDRAWAL_STATUS": DOMAIN_BANKING,
    "TRANSACTION_HISTORY": DOMAIN_BANKING,
    "TRANSACTION_REVERSED": DOMAIN_BANKING,
    "DUPLICATE_TRANSACTION": DOMAIN_BANKING,
    "WRONG_AMOUNT": DOMAIN_BANKING,
    "UNKNOWN_TRANSACTION": DOMAIN_BANKING,
    "DISPUTE_TRANSACTION": DOMAIN_BANKING,
    "FRAUD_REPORT": DOMAIN_BANKING,
    "SUSPICIOUS_ACTIVITY": DOMAIN_BANKING,
    "REFUND_AMOUNT_WRONG": DOMAIN_BANKING,
    "REFUND_FAILED": DOMAIN_BANKING,
    "REFUND_PENDING": DOMAIN_BANKING,
    "REFUND_RECEIVED": DOMAIN_BANKING,
    "MERCHANT_NOT_CREDITED": DOMAIN_BANKING,
    "KYC_FAILED": DOMAIN_BANKING,
    "KYC_STATUS": DOMAIN_BANKING,
    "KYC_UPDATE": DOMAIN_BANKING,
    "LOAN_STATUS": DOMAIN_BANKING,
    "LIMIT_QUERY": DOMAIN_BANKING,

    "KYC_DOCUMENTS": DOMAIN_FINANCIAL_KNOWLEDGE,
    "FINANCIAL_GUIDANCE": DOMAIN_FINANCIAL_KNOWLEDGE,

    "EMI_QUERY": DOMAIN_CALCULATION,
    "INTEREST_QUERY": DOMAIN_CALCULATION,

    "LOAN_ELIGIBILITY": DOMAIN_FINANCIAL_KNOWLEDGE,

    "SUPPORT_REQUEST": DOMAIN_SUPPORT,
}


# Strong markers for previously unsupported financial domains.
# These are deliberately broad domain signals, not transaction
# authorization rules.
MARKET_TERMS = (
    "stock",
    "stocks",
    "share price",
    "share market",
    "equity",
    "equities",
    "nifty",
    "sensex",
    "index",
    "indices",
    "nasdaq",
    "dow jones",
    "s&p 500",
    "etf",
    "forex",
    "currency pair",
    "usd/inr",
    "usd inr",
    "usd to inr",
    "dollar inr",
    "dollar to rupee",
    "dollar rupee",
    "eur/inr",
    "eur inr",
    "eur to inr",
    "crypto",
    "cryptocurrency",
    "bitcoin",
    "ethereum",
    "gold price",
    "silver price",
    "commodity",
    "commodities",
    "bond yield",
    "government security",
    "g-sec",
    "treasury bill",
    "t-bill",
    "market price",
    "share price",
    "ohlc",
    "candlestick",
    "chart",
    "price history",
    "historical price",
    "historical data",
    "trading volume",
    "market volume",
    "market breadth",
    "gainers",
    "losers",
    "52 week high",
    "52 week low",
)


REGULATORY_TERMS = (
    "sebi",
    "rbi",
    "irdai",
    "pfrda",
    "mca",
    "fema",
    "regulation",
    "regulations",
    "regulatory",
    "law",
    "laws",
    "legal rule",
    "rules",
    "circular",
    "master circular",
    "notification",
    "compliance",
    "disclosure requirement",
)


SCHEME_TERMS = (
    "government scheme",
    "government schemes",
    "post office scheme",
    "post office schemes",
    "post office savings",
    "small savings",
    "ppf",
    "nsc",
    "scss",
    "sukanya",
    "nps",
    "national pension",
    "kisan vikas",
    "mis scheme",
    "monthly income scheme",
)


PRODUCT_TERMS = (
    "credit card",
    "credit cards",
    "debit card",
    "bank account",
    "savings account",
    "current account",
    "salary account",
    "fixed deposit",
    "fd account",
    "recurring deposit",
    "rd account",
    "card eligibility",
    "card benefits",
    "card rewards",
    "cashback",
    "airport lounge",
    "annual fee",
    "joining fee",
    "forex fee",
)


CALCULATION_TERMS = (
    "calculate",
    "calculation",
    "calculator",
    "what if",
    "what happens if",
    "emi",
    "sip calculation",
    "lump sum",
    "lumpsum",
    "compound interest",
    "simple interest",
    "cagr",
    "xirr",
    "return calculation",
    "annualized return",
    "inflation adjustment",
    "yield calculation",
    "portfolio allocation",
    "drawdown",
    "volatility",
)


KNOWLEDGE_TERMS = (
    "what is",
    "what are",
    "explain",
    "meaning of",
    "how does",
    "how do",
    "basics",
    "learn",
    "guide",
    "difference between",
    "invest",
    "investment",
    "investing",
    "mutual fund",
    "mutual funds",
    "sip",
    "trading",
    "trade",
    "trader",
    "bond",
    "bonds",
    "portfolio",
    "diversification",
    "risk",
    "saving",
    "savings",
)


def _normalized(text: str) -> str:
    return " ".join(
        str(text).strip().lower().split()
    )


def _contains_any(text: str, terms) -> bool:
    return any(term in text for term in terms)


def _build_result(
    domain: str,
    reason: str,
    source: str,
) -> Dict[str, str]:
    return {
        "domain": domain,
        "reason": reason,
        "source": source,
    }


class FinAIDomainRouter:
    """
    Second-stage domain router for FinAI.

    This does not replace the trained intent classifier.
    It groups known intents into broader execution domains and
    provides conservative domain detection for unsupported queries.
    """

    def route(
        self,
        text: str,
        classified_intent: Optional[str] = None,
    ) -> Dict[str, str]:

        normalized = _normalized(text)

        if not normalized:
            return _build_result(
                DOMAIN_UNKNOWN,
                "empty_input",
                "domain_router",
            )

        if classified_intent:
            known_domain = KNOWN_INTENT_DOMAINS.get(
                str(classified_intent).strip().upper()
            )

            if known_domain:
                return _build_result(
                    known_domain,
                    "known_intent_domain_mapping",
                    "known_intent",
                )

        # Strong domain-specific knowledge has priority over the
        # broad knowledge vocabulary.
        if _contains_any(normalized, REGULATORY_TERMS):
            return _build_result(
                DOMAIN_REGULATORY_KNOWLEDGE,
                "regulatory_term",
                "deterministic_domain_rule",
            )

        if _contains_any(normalized, SCHEME_TERMS):
            return _build_result(
                DOMAIN_SCHEME_KNOWLEDGE,
                "scheme_term",
                "deterministic_domain_rule",
            )

        # Calculations are separated from educational questions.
        if _contains_any(normalized, CALCULATION_TERMS):
            return _build_result(
                DOMAIN_CALCULATION,
                "calculation_term",
                "deterministic_domain_rule",
            )

        # Product queries such as card/account eligibility or benefits.
        if _contains_any(normalized, PRODUCT_TERMS):
            return _build_result(
                DOMAIN_PRODUCT_COMPARISON,
                "product_term",
                "deterministic_domain_rule",
            )

        # Market terminology gets a dedicated domain.
        if _contains_any(normalized, MARKET_TERMS):
            return _build_result(
                DOMAIN_MARKET_DATA,
                "market_term",
                "deterministic_domain_rule",
            )

        if _contains_any(normalized, KNOWLEDGE_TERMS):
            return _build_result(
                DOMAIN_FINANCIAL_KNOWLEDGE,
                "financial_knowledge_term",
                "deterministic_domain_rule",
            )

        return _build_result(
            DOMAIN_UNKNOWN,
            "no_domain_match",
            "domain_router",
        )
