"""Structured investment, residency, regulatory and VDA scope for FinAI.

This module is a knowledge registry, not an execution or personalized-advice engine.
Regulatory/tax values carry source metadata and should be refreshed when source rules change.
"""
from __future__ import annotations
from typing import Any

DOMESTIC_INVESTMENT_AVENUES = [
{"group":"Equity & capital markets","items":["Direct equity shares — listed","Direct equity shares — unlisted","Mutual funds — equity","Mutual funds — debt","Mutual funds — index","Mutual funds — hybrid","Mutual funds — liquid","ETFs","Futures & Options (F&O)","Portfolio Management Services (PMS) — ₹50 lakh minimum under cited SEBI rule","Alternative Investment Funds (AIF) — Categories I/II/III; minimum commitment rules are fund/regulation-specific"]},
{"group":"Fixed income & debt","items":["Bank Fixed Deposits (FDs)","Recurring Deposits (RDs)","Corporate bonds","Non-Convertible Debentures (NCDs)","Commercial Papers","Government Securities (G-Secs)","Treasury Bills (T-Bills)","State Development Loans (SDLs)"]},
{"group":"Government savings & retirement","items":["Public Provident Fund (PPF)","Employee Provident Fund (EPF)","National Pension System (NPS)","Senior Citizens Savings Scheme (SCSS)","Sukanya Samriddhi Yojana (SSY)","National Savings Certificate (NSC)","Kisan Vikas Patra (KVP)"]},
{"group":"Precious metals & alternatives","items":["Digital Gold","Gold Mutual Funds / ETFs","Sovereign Gold Bonds (SGBs) — secondary-market availability depends on current issuance/trading status","Silver ETFs"]},
{"group":"Virtual Digital Assets","items":["Buying","Selling","Holding","Staking","Trading on platforms subject to applicable Indian AML/FIU requirements"]},
]

RESIDENT_LRS = {
"annual_limit_usd":250000,
"financial_year":"April–March",
"avenues":["Foreign equities (for example US stocks)","Global ETFs / mutual funds through eligible channels","Foreign-currency bank deposits where permitted","Overseas Direct Investment (ODI) in eligible foreign startups/subsidiaries","Permitted overseas investments under FEMA/LRS","GIFT City / IFSC investment routes"],
"note":"The USD 250,000 figure is the RBI LRS ceiling for resident individuals for permitted current/capital-account transactions; product-level eligibility remains instrument-specific.",
"source":"https://www.rbi.org.in/scripts/notificationuser.aspx?id=10192",
}

NRI_OCI = {
"accounts":["NRE — Non-Resident External; repatriation and tax treatment are subject to current FEMA/tax rules","NRO — Non-Resident Ordinary; repatriation is subject to applicable limits and conditions"],
"permitted":["Direct equities through applicable PIS/non-PIS routes and current rules","Mutual funds and ETFs subject to investor/product restrictions","PMS","AIFs","NRE FDs","FCNR(B) deposits","NRO FDs","G-Secs and T-Bills","Corporate bonds","NPS where eligibility rules permit","GIFT City / IFSC products where eligible"],
"restricted_or_prohibited":["New PPF accounts and specified small-savings products can be restricted after NRI status; existing-account treatment is rule-specific","Intraday trading, short selling and currency derivatives are subject to NRI-specific restrictions","Crypto activity must be evaluated under current AML/FIU, FEMA, banking and tax rules; do not encode a blanket 'NRO-only' rule without product-specific authority"],
"outside_india":["Foreign-earnings investment outside India is generally governed differently from Indian-source funds; FinAI must distinguish FEMA residence status, source of funds and tax residence rather than label all overseas income 'zero RBI restrictions' or 'not taxable in India'."],
}

REGULATORY_FRAMEWORK = [
{"domain":"Capital markets & equities","laws":["SEBI Act, 1992","Securities Contracts (Regulation) Act, 1956","Depositories Act, 1996","SEBI (Prohibition of Insider Trading) Regulations, 2015"],"regulators":["SEBI"]},
{"domain":"Forex & NRI investments","laws":["Foreign Exchange Management Act, 1999 (FEMA)","FEMA rules/regulations and RBI directions including LRS/PIS where applicable"],"regulators":["RBI"]},
{"domain":"Banking & savings","laws":["RBI Act, 1934","Banking Regulation Act, 1949","Government savings/post-office framework"],"regulators":["RBI","Ministry of Finance","India Post"]},
{"domain":"Taxation","laws":["Income-tax Act, 1961 and amendments","Black Money (Undisclosed Foreign Income and Assets) and Imposition of Tax Act, 2015","CGST Act, 2017"],"regulators":["CBDT","CBIC"]},
{"domain":"Retirement & insurance","laws":["PFRDA Act, 2013","IRDAI Act, 1999","EPF/EPS framework"],"regulators":["PFRDA","IRDAI","EPFO"]},
{"domain":"AML & consumer safety","laws":["Prevention of Money Laundering Act, 2002","Banning of Unregulated Deposit Schemes Act, 2019","Consumer Protection Act, 2019"],"regulators":["FIU-IND","Ministry of Consumer Affairs"]},
]

VDA_MECHANICS = {
"coins":["BTC","ETH","SOL"],
"tokens":["USDT","UNI","ERC-20 and other smart-contract tokens"],
"consensus":[
{"name":"Proof of Work (PoW)","description":"Miners use computational work to validate blocks and may earn block rewards/fees; Bitcoin is the canonical example."},
{"name":"Proof of Stake (PoS)","description":"Validators stake capital as collateral and participate in consensus; Ethereum and Solana are examples of PoS systems."},
],
"investment_and_yield":[
"Spot buying and holding",
"Native/on-chain staking",
"Liquid staking (for example Lido where applicable)",
"Exchange staking",
"Proof-of-Work mining using ASIC/GPU hardware",
"DeFi liquidity provision using automated market makers and constant-product pools such as x*y=k",
"Crypto lending / money markets such as Aave",
"Perpetual DEXs and leverage pools such as GMX — high-risk derivatives exposure",
"Regulated spot crypto ETFs where available in the relevant jurisdiction",
],
"smart_contracts":[
"ERC-20 token contracts can maintain address => balance mappings and transfer/approval logic",
"Multi-hop swaps can route Token A -> USDC -> Token C through intermediary pools",
],
"security_vectors":[
"Liquidity pull / rug pull — liquidity can be removed by an actor controlling the relevant assets/permissions",
"Honeypot — contract logic can restrict selling while allowing buying",
"Hidden minting — privileged functions can create additional supply",
],
}

VDA_TAX = {
"section_115BBH":"30% tax on VDA income, plus applicable surcharge and 4% cess; acquisition-cost treatment is subject to the statute.",
"section_194S":"TDS applies to qualifying VDA transfers under the applicable threshold/rules; the exact threshold and mechanism should be sourced by transaction type and current law.",
"loss_setoff":"Section 115BBH contains special restrictions on VDA loss set-off; FinAI should explain the statutory rule rather than generalize ordinary capital-loss treatment.",
"reporting":"Schedule VDA is used for transaction-wise VDA disclosure in applicable ITR forms.",
"current_source":"https://www.incometax.gov.in/iec/foportal/help/FileITR-2Online-FAQ",
"aml_source":"https://fiuindia.gov.in/pdfs/downloads/VDA08012026.pdf",
}

GLOBAL_ASSET_CLASSES = [
"Equities","ETFs","Indices","Government bonds","Corporate bonds","Bank deposits / fixed deposits","Mutual funds / pooled funds","REITs","Commodities","Foreign exchange",
]

GLOBAL_MARKET_REGISTRY = [
("India","IN","INR","NSE/BSE"),("United States","US","USD","NYSE/Nasdaq"),("Canada","CA","CAD","TSX"),
("United Kingdom","GB","GBP","LSE"),("Germany","DE","EUR","Xetra"),("France","FR","EUR","Euronext Paris"),("Switzerland","CH","CHF","SIX"),
("Japan","JP","JPY","Tokyo Stock Exchange"),("South Korea","KR","KRW","Korea Exchange"),("China","CN","CNY","Shanghai/Shenzhen"),("Hong Kong","HK","HKD","HKEX"),
("Singapore","SG","SGD","SGX"),("Australia","AU","AUD","ASX"),("New Zealand","NZ","NZD","NZX"),("Indonesia","ID","IDR","IDX"),
("Malaysia","MY","MYR","Bursa Malaysia"),("Thailand","TH","THB","SET"),("Vietnam","VN","VND","HOSE/HNX"),("Philippines","PH","PHP","PSE"),
("Israel","IL","ILS","TASE"),("United Arab Emirates","AE","AED","ADX/DFM"),("Saudi Arabia","SA","SAR","Tadawul"),
("Turkey","TR","TRY","Borsa Istanbul"),("Brazil","BR","BRL","B3"),("Mexico","MX","MXN","BMV"),("Argentina","AR","ARS","BYMA"),
("Chile","CL","CLP","Santiago"),("Colombia","CO","COP","BVC"),("South Africa","ZA","ZAR","JSE"),("Egypt","EG","EGP","EGX"),
("Nigeria","NG","NGN","NGX"),("Kenya","KE","KES","NSE Kenya"),
]

USER_REQUESTED_GLOBAL_EXAMPLE = {
"country":"Argentina",
"instrument_example":"Foreign fixed-term deposit / FD",
"status":"CONDITIONAL",
"required_checks":["Non-resident eligibility at the specific bank","Argentine FX/capital controls","KYC/source-of-funds requirements","Deposit insurance/product terms","Currency conversion and repatriation","Indian FEMA/LRS applicability","Indian tax and foreign-asset reporting"],
}

VERIFIED_NOTES = {
"lrs":"RBI documents a USD 250,000 per financial year LRS limit for resident individuals for permitted transactions.",
"pms":"SEBI materials state the PMS minimum investment amount is INR 50 lakh.",
"vda_tax":"Income Tax Department currently states 30% VDA tax under section 115BBH plus applicable surcharge and 4% cess and provides Schedule VDA guidance.",
"fiu_vda":"FIU-IND's January 2026 AML/CFT guidance covers reporting entities providing services related to VDAs.",
}

def investment_scope() -> dict[str, Any]:
    return {
        "domestic":DOMESTIC_INVESTMENT_AVENUES,
        "resident_lrs":RESIDENT_LRS,
        "nri_oci":NRI_OCI,
        "regulatory_framework":REGULATORY_FRAMEWORK,
        "vda_mechanics":VDA_MECHANICS,
        "vda_tax":VDA_TAX,
        "global_asset_classes":GLOBAL_ASSET_CLASSES,
        "global_market_registry":[{"country":n,"code":c,"currency":cur,"market":m} for n,c,cur,m in GLOBAL_MARKET_REGISTRY],
        "global_example":USER_REQUESTED_GLOBAL_EXAMPLE,
        "verified_notes":VERIFIED_NOTES,
    }
