"""Global investment universe and Indian-resident eligibility metadata.

This is a registry, not a broker/order system. Live prices/yields should be
provided by market-data connectors; eligibility is intentionally marked
conditional where product-specific verification is required.
"""
from __future__ import annotations

from typing import Any, Dict, List

COUNTRIES = [
    ("India", "IN", "INR", "NSE/BSE", "Domestic"),
    ("United States", "US", "USD", "NYSE/Nasdaq", "United States"),
    ("Canada", "CA", "CAD", "TSX", "North America"),
    ("United Kingdom", "GB", "GBP", "LSE", "Europe"),
    ("Germany", "DE", "EUR", "Xetra", "Europe"),
    ("France", "FR", "EUR", "Euronext Paris", "Europe"),
    ("Switzerland", "CH", "CHF", "SIX", "Europe"),
    ("Netherlands", "NL", "EUR", "Euronext Amsterdam", "Europe"),
    ("Italy", "IT", "EUR", "Borsa Italiana", "Europe"),
    ("Spain", "ES", "EUR", "BME", "Europe"),
    ("Ireland", "IE", "EUR", "Euronext Dublin", "Europe"),
    ("Norway", "NO", "NOK", "Oslo Bors", "Europe"),
    ("Sweden", "SE", "SEK", "Nasdaq Stockholm", "Europe"),
    ("Denmark", "DK", "DKK", "Nasdaq Copenhagen", "Europe"),
    ("Finland", "FI", "EUR", "Nasdaq Helsinki", "Europe"),
    ("Japan", "JP", "JPY", "Tokyo Stock Exchange", "Asia-Pacific"),
    ("South Korea", "KR", "KRW", "Korea Exchange", "Asia-Pacific"),
    ("China", "CN", "CNY", "Shanghai/Shenzhen", "Asia-Pacific"),
    ("Hong Kong", "HK", "HKD", "HKEX", "Asia-Pacific"),
    ("Taiwan", "TW", "TWD", "Taiwan Stock Exchange", "Asia-Pacific"),
    ("Singapore", "SG", "SGD", "SGX", "Asia-Pacific"),
    ("Australia", "AU", "AUD", "ASX", "Asia-Pacific"),
    ("New Zealand", "NZ", "NZD", "NZX", "Asia-Pacific"),
    ("Indonesia", "ID", "IDR", "IDX", "Asia-Pacific"),
    ("Malaysia", "MY", "MYR", "Bursa Malaysia", "Asia-Pacific"),
    ("Thailand", "TH", "THB", "SET", "Asia-Pacific"),
    ("Vietnam", "VN", "VND", "HOSE/HNX", "Asia-Pacific"),
    ("Philippines", "PH", "PHP", "PSE", "Asia-Pacific"),
    ("Israel", "IL", "ILS", "TASE", "Middle East"),
    ("United Arab Emirates", "AE", "AED", "ADX/DFM", "Middle East"),
    ("Saudi Arabia", "SA", "SAR", "Tadawul", "Middle East"),
    ("Turkey", "TR", "TRY", "Borsa Istanbul", "Europe/Middle East"),
    ("Brazil", "BR", "BRL", "B3", "Latin America"),
    ("Mexico", "MX", "MXN", "BMV", "Latin America"),
    ("Argentina", "AR", "ARS", "BYMA", "Latin America"),
    ("Chile", "CL", "CLP", "Santiago", "Latin America"),
    ("Colombia", "CO", "COP", "BVC", "Latin America"),
    ("South Africa", "ZA", "ZAR", "JSE", "Africa"),
    ("Egypt", "EG", "EGP", "EGX", "Africa"),
    ("Nigeria", "NG", "NGN", "NGX", "Africa"),
    ("Kenya", "KE", "KES", "NSE Kenya", "Africa"),
]

ASSET_CLASSES = [
    {"id": "equity", "label": "Equities", "description": "Listed company shares and ADR/GDR-style instruments where accessible."},
    {"id": "etf", "label": "ETFs", "description": "Exchange-traded funds; availability depends on venue and Indian investor access."},
    {"id": "index", "label": "Indices", "description": "Market indices for research and benchmark comparison; an index itself is not necessarily investable."},
    {"id": "government_bond", "label": "Government bonds", "description": "Sovereign bills and bonds, subject to local and Indian investor rules."},
    {"id": "corporate_bond", "label": "Corporate bonds", "description": "Issuer debt securities, subject to local market access and intermediary rules."},
    {"id": "deposit", "label": "Bank deposits / FD", "description": "Foreign bank time deposits; account opening and exchange-control rules vary."},
    {"id": "fund", "label": "Funds", "description": "Mutual funds and other pooled vehicles."},
    {"id": "reit", "label": "REITs", "description": "Listed real-estate investment vehicles where available."},
    {"id": "commodity", "label": "Commodities", "description": "Gold, energy, agricultural and industrial commodity exposures."},
    {"id": "forex", "label": "Currencies", "description": "FX market data for research; retail investment access is jurisdiction-dependent."},
]

SPECIAL_NOTES = {
    "AR": {
        "status": "CONDITIONAL",
        "summary": "Argentine fixed-term deposits exist, but non-resident access, foreign-exchange controls, repatriation and bank KYC must be verified for the specific bank and transaction.",
        "verification_sources": ["https://www.bcra.gob.ar/"],
    },
    "US": {
        "status": "CONDITIONAL",
        "summary": "Foreign access to US securities is commonly available through eligible intermediaries, but instrument, broker, tax and Indian overseas-investment rules must be checked.",
        "verification_sources": ["https://www.treasury.gov/"],
    },
    "GB": {
        "status": "CONDITIONAL",
        "summary": "UK-listed securities and government debt can be researched globally; investor, intermediary, tax and Indian overseas-investment requirements remain instrument-specific.",
        "verification_sources": ["https://www.dmo.gov.uk/"],
    },
    "JP": {
        "status": "CONDITIONAL",
        "summary": "Japanese listed securities and government debt are accessible through eligible international channels in some circumstances; verify intermediary and tax requirements.",
        "verification_sources": ["https://www.mof.go.jp/"],
    },
    "SG": {
        "status": "CONDITIONAL",
        "summary": "Singapore securities and government securities have foreign-investor routes for some instruments; verify account, tax and Indian overseas-investment requirements.",
        "verification_sources": ["https://www.mas.gov.sg/"],
    },
}

def list_global_markets() -> List[Dict[str, Any]]:
    return [
        {"country": n, "country_code": c, "currency": cur, "primary_market": market, "region": region,
         "asset_classes": [a["id"] for a in ASSET_CLASSES]}
        for n, c, cur, market, region in COUNTRIES
    ]

def global_catalog() -> Dict[str, Any]:
    return {"countries": list_global_markets(), "asset_classes": ASSET_CLASSES, "investor_profile": "Indian resident individual", "scope_note": "Country coverage is a research registry. Instrument-level eligibility must be verified before execution."}

def eligibility(country_code: str, asset_class: str) -> Dict[str, Any]:
    code = country_code.upper()
    country = next((row for row in COUNTRIES if row[1] == code), None)
    if not country:
        raise ValueError("Unknown country code.")
    note = SPECIAL_NOTES.get(code, {})
    if code == "IN":
        status = "DOMESTIC"
    else:
        status = note.get("status", "CONDITIONAL")
    return {
        "country": country[0], "country_code": code, "asset_class": asset_class,
        "investor": "Indian resident individual", "status": status,
        "summary": note.get("summary", "Instrument-level eligibility, intermediary onboarding, Indian FEMA/LRS rules, local rules and tax treatment must be verified."),
        "checks": [
            "Indian FEMA / overseas-investment rules",
            "LRS applicability and remaining annual limit where relevant",
            "Local foreign-investor eligibility",
            "Bank/broker KYC and account-opening requirements",
            "Currency conversion and repatriation rules",
            "Foreign withholding and Indian tax/reporting treatment",
        ],
        "verification_sources": note.get("verification_sources", []),
    }
