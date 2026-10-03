"""Source-linked Indian finance regulation and workflow knowledge.

This module deliberately separates descriptive regulatory information from
live approvals/eligibility. Official regulator and government sources remain
authoritative for any real transaction or filing.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class RegulationTopic:
    topic_id: str
    title: str
    category: str
    answer: str
    steps: Tuple[str, ...]
    authority: str
    official_url: str
    updated: str
    caveat: str


SEBI_URL = "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListingLegal=yes&sid=1&smid=0&ssid=3"
ICDR_URL = "https://www.sebi.gov.in/legal/regulations/mar-2026/securities-and-exchange-board-of-india-issue-of-capital-and-disclosure-requirements-regulations-2018-last-amended-on-march-21-2026-_100581.html"
LODR_URL = "https://www.sebi.gov.in/legal/regulations/jul-2026/securities-and-exchange-board-of-india-listing-obligations-and-disclosure-requirements-regulations-2015-last-amended-on-july-14-2026-_102974.html"
FPI_URL = "https://www.sebi.gov.in/legal/regulations/jul-2026/securities-and-exchange-board-of-india-foreign-portfolio-investors-regulations-2019-last-amended-on-july-07-2026-_102902.html"
MF_URL = "https://www.sebi.gov.in/legal/regulations/jul-2026/securities-and-exchange-board-of-india-mutual-funds-regulations-2026-last-amended-on-july-7-2026-_102780.html"
RBI_FI_URL = "https://www.rbi.org.in/scripts/FS_Notification.aspx?Id=11200"
RBI_RETAIL_URL = "https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=50706"
FDI_URL = "https://www.dpiit.gov.in/offerings/initiative/details/foreign-direct-investment-gTM4EjNtQWa"
FIU_URL = "https://fiuindia.gov.in/files/downloads/downloads.html"
VDA_SNAPSHOT_URL = "https://sansad.in/getFile/loksabhaquestions/annex/187/AU5805_lMTYNK.pdf?source=pqals"
ETF_URL = "https://investor.sebi.gov.in/exchange_traded_fund.html"


TOPICS = (
    RegulationTopic(
        "mainboard_ipo",
        "Main-board equity IPO",
        "Listing",
        "An eligible unlisted issuer can seek public listing through an IPO under the SEBI ICDR framework, subject to eligibility, disclosures, intermediaries, issue structure, exchange requirements and company-law requirements.",
        (
            "Define security and proposed issue structure.",
            "Check current ICDR eligibility and public-offer conditions.",
            "Appoint the required intermediaries and conduct due diligence.",
            "Prepare and file the offer document through the prescribed process.",
            "Complete issue, allotment and exchange-listing formalities.",
            "Maintain continuing listed-entity obligations after listing.",
        ),
        "SEBI",
        ICDR_URL,
        "21-03-2026",
        "Exact eligibility and disclosure requirements depend on the issuer and the current regulations.",
    ),
    RegulationTopic(
        "sme_ipo",
        "SME IPO",
        "Listing",
        "Eligible smaller issuers can use a recognised SME exchange platform through the applicable SEBI ICDR and exchange framework.",
        (
            "Check SME platform eligibility.",
            "Select the exchange and required intermediaries.",
            "Prepare the offer document and complete due diligence.",
            "Conduct the issue and allotment under the SME framework.",
            "Complete exchange listing and post-listing requirements.",
        ),
        "SEBI / Recognised Stock Exchange",
        ICDR_URL,
        "21-03-2026",
        "SME eligibility, market-making and issue requirements must be verified for the current issue.",
    ),
    RegulationTopic(
        "igp",
        "Innovators Growth Platform",
        "Listing",
        "The Innovators Growth Platform is a specialised listing route for eligible issuers, including specified routes involving an issue or listing without a public offer.",
        (
            "Check current IGP issuer and investor eligibility.",
            "Confirm the applicable shareholding and disclosure conditions.",
            "Complete the prescribed intermediary and exchange process.",
            "Complete listing and trading admission requirements.",
        ),
        "SEBI / Recognised Stock Exchange",
        ICDR_URL,
        "21-03-2026",
        "IGP requirements differ from main-board and SME routes.",
    ),
    RegulationTopic(
        "post_listing_fundraising",
        "Post-listing capital raising",
        "Listing",
        "A listed issuer may use applicable mechanisms such as follow-on public offers, rights issues, preferential issues, qualified institutions placement or bonus issues when the relevant rules and conditions are met.",
        (
            "Identify the security and investor class.",
            "Select the permitted capital-raising route.",
            "Check ICDR, company-law and exchange requirements.",
            "Prepare disclosures and approvals.",
            "Complete issue, allocation, filings and exchange actions.",
        ),
        "SEBI",
        ICDR_URL,
        "2026",
        "These are post-listing fundraising mechanisms, not substitutes for an initial-listing route.",
    ),
    RegulationTopic(
        "debt_listing",
        "Debt-security listing",
        "Listing",
        "Debt securities have their own issue, disclosure and listing requirements under the applicable SEBI and exchange framework.",
        (
            "Identify the debt-security type and investor route.",
            "Check current SEBI issue/listing rules.",
            "Prepare disclosures and appoint required intermediaries.",
            "Complete issue, allotment and listing.",
        ),
        "SEBI / Recognised Stock Exchange",
        SEBI_URL,
        "2026",
        "Debt listing is regulated separately from equity IPOs.",
    ),
    RegulationTopic(
        "lodr",
        "SEBI LODR",
        "SEBI Regulation",
        "The Listing Obligations and Disclosure Requirements framework sets continuing obligations for listed entities, including disclosures and governance requirements.",
        (
            "Identify the listed-entity category and security.",
            "Map events and periodic disclosures to the applicable LODR provisions.",
            "Maintain governance and exchange-reporting controls.",
            "File required disclosures within the applicable timelines.",
        ),
        "SEBI",
        LODR_URL,
        "14-07-2026",
        "The applicable requirement depends on the entity, security and event.",
    ),
    RegulationTopic(
        "icdr",
        "SEBI ICDR",
        "SEBI Regulation",
        "The ICDR framework governs issue and capital-raising requirements for specified securities, including IPOs and several post-listing issues.",
        (
            "Identify the issue type.",
            "Determine applicable eligibility and disclosures.",
            "Prepare the issue document and complete due diligence.",
            "Complete the prescribed filing, pricing, allotment and listing steps.",
        ),
        "SEBI",
        ICDR_URL,
        "21-03-2026",
        "Always use the latest regulation and circulars for a live transaction.",
    ),
    RegulationTopic(
        "mutual_funds",
        "Mutual Funds Regulations 2026",
        "SEBI Regulation",
        "SEBI's 2026 Mutual Funds Regulations form the current framework for mutual funds and scheme-level governance and disclosure.",
        (
            "Identify the scheme and category.",
            "Read current scheme documents and disclosures.",
            "Review risk, costs, portfolio and liquidity.",
            "Use the AMC or regulated transaction platform.",
        ),
        "SEBI",
        MF_URL,
        "07-07-2026",
        "Scheme-level facts and circulars must be checked for a current comparison.",
    ),
    RegulationTopic(
        "fpi",
        "Foreign Portfolio Investment",
        "Foreign Investment",
        "Eligible non-resident investors can access Indian securities through the FPI framework and related foreign-exchange rules.",
        (
            "Determine whether the investor qualifies as an FPI.",
            "Complete prescribed registration and onboarding.",
            "Check permitted instruments, investment limits and disclosure/reporting rules.",
            "Use prescribed custodial and authorised channels.",
            "Maintain ownership and regulatory records.",
        ),
        "SEBI / RBI",
        FPI_URL,
        "07-07-2026",
        "Eligibility, beneficial ownership and limits are transaction-specific.",
    ),
    RegulationTopic(
        "fdi_automatic",
        "Foreign Direct Investment — Automatic Route",
        "Foreign Investment",
        "Eligible foreign investment in an Indian sector can use the automatic route when the sector, cap and applicable conditions permit it.",
        (
            "Identify sector and applicable foreign-investment cap.",
            "Check entry route and performance conditions.",
            "Complete pricing and reporting through authorised banking/RBI channels.",
            "Complete corporate, beneficial-owner and record-keeping requirements.",
        ),
        "Government of India / RBI / DPIIT",
        FDI_URL,
        "Current policy",
        "Sectoral caps and conditions vary by activity and must be checked before investment.",
    ),
    RegulationTopic(
        "fdi_government",
        "Foreign Direct Investment — Government Route",
        "Foreign Investment",
        "Foreign investments requiring prior Government approval must follow the prescribed approval process before implementation.",
        (
            "Identify why the investment falls under the approval route.",
            "Prepare the required application and supporting information.",
            "Obtain approval before implementing the investment where required.",
            "Complete pricing, reporting and corporate-law requirements.",
        ),
        "Government of India / DPIIT",
        FDI_URL,
        "Current policy",
        "Approval authority and conditions vary by sector and transaction.",
    ),
    RegulationTopic(
        "nri_oci",
        "NRI / OCI investment",
        "Foreign Investment",
        "NRIs and OCIs have specific repatriation and non-repatriation investment routes for Indian securities and entities.",
        (
            "Determine NRI/OCI status and repatriation intent.",
            "Select a permitted security or entity route.",
            "Use the designated authorised-dealer banking route where required.",
            "Follow ownership, payment and repatriation conditions.",
        ),
        "RBI",
        RBI_FI_URL,
        "Current direction",
        "Different instruments use different schedules and repatriation rules.",
    ),
    RegulationTopic(
        "ifsc",
        "IFSC investment and financial services",
        "Investment",
        "An IFSC is a distinct regulated financial-services environment with product-specific permissions and regulator responsibilities.",
        (
            "Identify whether the activity is inside an IFSC.",
            "Determine the product and investor category.",
            "Check IFSCA/SEBI/RBI permissions and reporting.",
            "Maintain tax, AML and transaction records.",
        ),
        "IFSCA / SEBI / RBI",
        "https://www.ifsca.gov.in/LegalDatabase",
        "Current framework",
        "IFSC status does not create a blanket exemption from Indian regulation.",
    ),
    RegulationTopic(
        "inr_investing",
        "INR investment routes in India",
        "Investment",
        "Residents can invest INR through bank deposits, government securities, mutual funds, ETFs, listed shares, bonds and other permitted instruments.",
        (
            "Define objective, horizon, liquidity and risk constraints.",
            "Select an instrument and current terms.",
            "Complete KYC and transaction onboarding.",
            "Record price, costs, ownership and tax information.",
        ),
        "RBI / SEBI / Issuer",
        SEBI_URL,
        "2026",
        "Rates, charges, eligibility and tax treatment are time-sensitive.",
    ),
    RegulationTopic(
        "etf",
        "Exchange-Traded Funds",
        "Investment Product",
        "An ETF is a pooled investment product whose units trade on an exchange and whose market price can differ from NAV.",
        (
            "Select the ETF and inspect its underlying index or assets.",
            "Review costs, tracking difference, liquidity and bid-ask spread.",
            "Use a demat-enabled broker/exchange route.",
            "Monitor market price against available NAV information.",
        ),
        "SEBI Investor",
        ETF_URL,
        "Current investor education",
        "Specific ETF terms and liquidity vary by scheme.",
    ),
    RegulationTopic(
        "crypto_vda_india",
        "Crypto / VDA regulatory position in India",
        "Crypto Regulation",
        "The March 2026 Government snapshot states that VDA service providers are reporting entities under the PMLA framework and that 54 were registered with FIU-IND as of 09-03-2026. The Government also states that this should not be interpreted as a general licence or endorsement.",
        (
            "Check the provider's current FIU-IND status.",
            "Check current product and account restrictions.",
            "Complete KYC and retain transaction records.",
            "Track current tax/TDS and reporting requirements.",
            "Re-check official Government/FIU information before relying on the status.",
        ),
        "FIU-IND / Government of India",
        VDA_SNAPSHOT_URL,
        "09-03-2026 snapshot",
        "The snapshot is historical; reporting-entity registration is not blanket product approval.",
    ),
    RegulationTopic(
        "create_token",
        "Creating a cryptocurrency or token",
        "Crypto Mechanics",
        "A cryptocurrency can mean a native asset on its own blockchain, while a token is commonly deployed on an existing blockchain through smart-contract or native-token mechanisms.",
        (
            "Choose a native blockchain or an existing-chain token.",
            "Define supply, issuance, decimals, transfers, permissions and governance.",
            "Implement consensus/network infrastructure or audited smart-contract code.",
            "Test security, key management and upgrade controls.",
            "Design custody, treasury, disclosures and incident response.",
            "Review jurisdiction-specific securities, tax, AML and consumer rules before offering the asset.",
        ),
        "Technical design + applicable jurisdictional authorities",
        FIU_URL,
        "Current framework",
        "Technical deployment does not by itself establish that public offering, sale or exchange is legally permitted.",
    ),
    RegulationTopic(
        "mining",
        "Proof-of-work mining economics",
        "Crypto Mechanics",
        "Mining economics depend on block rewards and transaction fees, network difficulty/hash rate, hardware efficiency, electricity cost, pool fees, uptime and asset price.",
        (
            "Measure hardware hash rate and electrical power.",
            "Read current network difficulty, hash rate and reward data.",
            "Estimate expected production from your network share.",
            "Subtract electricity, pool fees, hardware depreciation and downtime.",
            "Stress-test the result against changes in price and difficulty.",
        ),
        "Protocol/network data + mining-pool disclosures",
        "https://mempool.space/docs/api/rest",
        "Dynamic",
        "Expected mining income is probabilistic and not a guaranteed profit figure.",
    ),
    RegulationTopic(
        "rbi_retail_direct",
        "RBI Retail Direct",
        "Government Securities",
        "RBI Retail Direct provides an access route for eligible retail investors to specified government securities.",
        (
            "Open the eligible retail-direct account.",
            "Review available government securities and terms.",
            "Place purchase instructions through the platform.",
            "Monitor interest and maturity or permitted secondary-market actions.",
        ),
        "RBI",
        RBI_RETAIL_URL,
        "Current platform",
        "Security-specific and platform-specific conditions apply.",
    ),
)


def list_regulations(category: Optional[str] = None) -> List[Dict[str, object]]:
    items = TOPICS
    if category:
        normalized = category.strip().lower()
        items = tuple(item for item in items if item.category.lower() == normalized)
    return [asdict(item) for item in items]


def search_regulations(query: str) -> List[Dict[str, object]]:
    normalized = " ".join(str(query).strip().lower().split())
    if not normalized:
        return []

    tokens = [token for token in normalized.split() if len(token) >= 3]
    scored: List[tuple[int, RegulationTopic]] = []

    for item in TOPICS:
        searchable = " ".join(
            (
                item.topic_id,
                item.title,
                item.category,
                item.answer,
                " ".join(item.steps),
            )
        ).lower()
        exact = 12 if normalized in searchable else 0
        token_score = sum(2 for token in tokens if token in searchable)
        score = exact + token_score
        if score:
            scored.append((score, item))

    scored.sort(key=lambda pair: (-pair[0], pair[1].topic_id))
    return [asdict(item) for _, item in scored[:25]]
