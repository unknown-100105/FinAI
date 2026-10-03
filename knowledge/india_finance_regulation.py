"""India finance regulatory and transaction-route knowledge, with official sources.

These are source-guided educational workflows. They do not constitute legal advice,
a securities approval, or a filing submission.
"""

from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Dict, List, Tuple, Optional


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


SEBI_REGS = "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=2&smid=0&ssid=3"
ICDR_2026 = "https://www.sebi.gov.in/legal/regulations/mar-2026/securities-and-exchange-board-of-india-issue-of-capital-and-disclosure-requirements-regulations-2018-last-amended-on-march-21-2026-_100581.html"
LODR_2026 = "https://www.sebi.gov.in/legal/regulations/jul-2026/securities-and-exchange-board-of-india-listing-obligations-and-disclosure-requirements-regulations-2015-last-amended-on-july-14-2026-_102974.html"
FPI_2026 = "https://www.sebi.gov.in/legal/regulations/jul-2026/securities-and-exchange-board-of-india-foreign-portfolio-investors-regulations-2019-last-amended-on-july-07-2026-_102902.html"
MF_2026 = "https://www.sebi.gov.in/legal/regulations/jul-2026/securities-and-exchange-board-of-india-mutual-funds-regulations-2026-last-amended-on-july-7-2026-_102780.html"
AIF_2026 = "https://www.sebi.gov.in/legal/regulations/jul-2026/securities-and-exchange-board-of-india-alternative-investment-funds-regulations-2012-last-amended-on-july-14-2026-_102975.html"
RBI_FI = "https://www.rbi.org.in/scripts/FS_Notification.aspx?Id=11200"
RBI_RETAIL_DIRECT = "https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=50706"
FIU_VDA = "https://fiuindia.gov.in/files/downloads/downloads.html"
VDA_REGISTER = "https://sansad.in/getFile/loksabhaquestions/annex/187/AU5805_lMTYNK.pdf?source=pqals"


TOPICS = (
    RegulationTopic(
        "list_equity_mainboard", "Main-board equity IPO", "Listing",
        "An unlisted issuer can seek a public listing through an Initial Public Offer (IPO) under the SEBI ICDR framework, subject to eligibility, disclosures, intermediaries, pricing and exchange requirements.",
        ("Choose the security and proposed issue structure.", "Check ICDR eligibility and public-offer conditions.", "Appoint required intermediaries such as a merchant banker.", "Prepare and file the offer document through the prescribed process.", "Complete due diligence, observations, marketing and issue process.", "Obtain exchange approval and list the securities after allotment and post-issue compliance."),
        "SEBI", ICDR_2026, "21-03-2026",
        "Exact eligibility, disclosures and issue structure depend on the issuer and current ICDR provisions."),
    RegulationTopic(
        "list_sme_ipo", "SME IPO", "Listing",
        "Eligible smaller issuers can pursue an IPO and listing on an SME platform under the SEBI ICDR framework and the applicable exchange rules.",
        ("Confirm the issuer is eligible for the SME platform.", "Select the SME exchange/platform and intermediaries.", "Prepare the offer document and complete due diligence.", "Conduct the public issue under the prescribed SME rules.", "Complete allotment and exchange listing formalities."),
        "SEBI / Recognized Stock Exchange", ICDR_2026, "21-03-2026",
        "SME eligibility, issue size, market-maker and other requirements must be checked against current rules."),
    RegulationTopic(
        "list_igp", "Innovators Growth Platform listing", "Listing",
        "The Innovators Growth Platform (IGP) provides a distinct route for eligible issuers, including listing with an issue or, in specified circumstances, listing without a public offer.",
        ("Check IGP eligibility and investor/issuer conditions.", "Meet the pre-issue or pre-listing shareholding and disclosure conditions applicable to IGP.", "Use the prescribed exchange and intermediary process.", "Complete listing/trading admission requirements."),
        "SEBI", ICDR_2026, "21-03-2026",
        "IGP is a specialized platform; eligibility is materially different from the main-board IPO route."),
    RegulationTopic(
        "listed_fundraising", "Fundraising after listing", "Listing",
        "Once listed, a company can use regulated capital-raising mechanisms such as follow-on public issues, rights issues, preferential issues, qualified institutions placement and bonus issues when the relevant rules and conditions are met.",
        ("Identify the security and investor class.", "Check the applicable ICDR and company-law route.", "Prepare disclosures/resolutions.", "Complete pricing/allocation and filing requirements.", "Complete exchange and depository actions."),
        "SEBI", ICDR_2026, "21-03-2026",
        "These are post-listing capital-raising mechanisms; they are not interchangeable with an initial listing route."),
    RegulationTopic(
        "list_debt", "Debt-security listing", "Listing",
        "Debt securities have separate issue-and-listing frameworks, including SEBI rules for non-convertible securities and exchange listing requirements.",
        ("Identify debt security type and investor route.", "Check issue-and-listing regulations and disclosure requirements.", "Appoint required intermediaries and prepare offer/placement documents.", "Complete issue, allotment and listing."),
        "SEBI", "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=2&smid=0&ssid=3", "2026",
        "Debt listing is a different regulatory path from an equity IPO."),
    RegulationTopic(
        "sebi_lodr", "SEBI LODR", "SEBI Regulation",
        "The Listing Obligations and Disclosure Requirements framework governs continuing obligations of listed entities, including disclosures, governance and compliance requirements.",
        ("Identify the security and listed-entity category.", "Check the applicable LODR provision and periodic disclosure.", "Maintain board, governance and exchange-reporting controls.", "File disclosures through the exchange channels within the applicable timelines."),
        "SEBI", LODR_2026, "14-07-2026",
        "LODR requirements depend on the entity, security and event."),
    RegulationTopic(
        "sebi_icdr", "SEBI ICDR", "SEBI Regulation",
        "The ICDR Regulations govern issue and capital-raising requirements for specified securities, including public offers, SME IPOs and several post-listing issues.",
        ("Identify the issue type.", "Determine applicable eligibility and disclosures.", "Prepare the offer/issue document.", "Complete intermediary, due-diligence and filing requirements."),
        "SEBI", ICDR_2026, "21-03-2026",
        "Always use the latest SEBI text and circulars for a live transaction."),
    RegulationTopic(
        "sebi_fpi", "Foreign Portfolio Investor route", "Foreign Investment",
        "Eligible non-resident investors can access Indian listed securities through the FPI framework administered by SEBI and linked foreign-exchange rules.",
        ("Determine whether the investor qualifies as an FPI.", "Complete registration/onboarding with the designated mechanisms.", "Use permitted instruments and comply with investment limits and disclosure/reporting rules.", "Route funds and trades through the prescribed custodial/authorized channels.", "Reconcile ownership and regulatory reporting."),
        "SEBI / RBI", FPI_2026, "07-07-2026",
        "FPI eligibility, limits, beneficial ownership and sectoral rules must be checked for the current transaction."),
    RegulationTopic(
        "fdi_automatic", "FDI — Automatic Route", "Foreign Investment",
        "Foreign direct investment in an eligible Indian sector can be made without prior Central Government approval when the sector, cap and conditions fall within the automatic route.",
        ("Identify the business sector and applicable FDI cap.", "Check entry route and any performance-linked conditions.", "Complete pricing, reporting and documentation through the authorized bank/RBI channels.", "Complete company-law and beneficial-owner compliance."),
        "RBI / DPIIT / Government of India", RBI_FI, "Current direction",
        "Entry route and sectoral caps vary by sector and policy; the current FDI policy must be checked."),
    RegulationTopic(
        "fdi_government", "FDI — Government Route", "Foreign Investment",
        "Foreign investment requiring prior Government approval must follow the prescribed approval process before the investment is implemented.",
        ("Identify the sector and reason approval is triggered.", "Prepare the prescribed application and supporting information.", "Obtain approval before executing the investment where required.", "Complete pricing, reporting and corporate-law steps."),
        "Government of India / RBI", "https://www.dpiit.gov.in/offerings/initiative/details/foreign-direct-investment-gTM4EjNtQWa", "Current policy source",
        "Sectoral restrictions, approval authority and conditions vary."),
    RegulationTopic(
        "nri_oci", "NRI / OCI investment routes", "Foreign Investment",
        "NRIs and OCIs have specific repatriation and non-repatriation investment routes for Indian securities and entities under foreign-exchange rules.",
        ("Determine NRI/OCI status and repatriation intent.", "Select the permitted security/entity route.", "Use the designated banking/authorized-dealer channel.", "Follow ownership, payment and repatriation conditions."),
        "RBI", RBI_FI, "Current direction",
        "Different schedules and payment/repatriation rules apply to different instruments."),
    RegulationTopic(
        "ifsc_investing", "Investing through an IFSC", "Foreign Investment",
        "The IFSC framework provides a regulated financial-services environment with its own permissions and routes; investment into India can also interact with RBI/SEBI rules depending on the activity.",
        ("Identify whether the activity is in an IFSC and which regulator applies.", "Select the permitted product and investor category.", "Complete the IFSC/SEBI/RBI onboarding and reporting requirements.", "Maintain the relevant tax, AML and reporting records."),
        "IFSCA / SEBI / RBI", "https://www.ifsca.gov.in/LegalDatabase", "Current framework",
        "IFSC permissions are product-specific and should not be confused with a blanket exemption from Indian rules."),
    RegulationTopic(
        "india_inr_investing", "INR investment routes in India", "Investment",
        "Residents can invest INR through bank deposits, government securities, mutual funds, ETFs, listed shares, bonds and other products offered under the applicable regulated or statutory framework.",
        ("Define goal, horizon, liquidity and risk constraints.", "Select an instrument whose rules match the goal.", "Use a regulated intermediary/issuer and complete KYC.", "Record transaction price, costs, tax information and ownership."),
        "RBI / SEBI / Issuers", SEBI_REGS, "2026",
        "Product eligibility, rates, charges and tax treatment are time-sensitive."),
    RegulationTopic(
        "etf", "Exchange-Traded Funds", "Investment Product",
        "An ETF is a pooled investment product whose units trade on a stock exchange. ETF market price can move with trading and can differ from NAV.",
        ("Select the ETF and inspect its underlying index/assets.", "Review expense ratio, tracking difference, liquidity and bid-ask spread.", "Use a demat-enabled broker/exchange route.", "Monitor market price versus indicative/NAV information."),
        "SEBI Investor", "https://investor.sebi.gov.in/exchange_traded_fund.html", "Current investor education",
        "ETF costs, liquidity and suitability depend on the specific ETF."),
    RegulationTopic(
        "mutual_funds_2026", "Mutual Funds Regulations 2026", "SEBI Regulation",
        "SEBI issued the Mutual Funds Regulations, 2026, with the current regulation set and amendments determining the regulatory framework for mutual funds.",
        ("Identify the fund category and scheme.", "Read the scheme information and current disclosures.", "Check risk, costs, portfolio and liquidity.", "Use the AMC/regulated platform for transactions."),
        "SEBI", MF_2026, "07-07-2026",
        "Scheme-level facts and current circulars remain necessary for a live comparison."),
    RegulationTopic(
        "aif_2026", "Alternative Investment Funds", "SEBI Regulation",
        "AIFs are pooled vehicles governed by a separate SEBI framework with category-specific requirements.",
        ("Determine the AIF category.", "Review the placement memorandum and eligibility.", "Check manager, strategy, fees, liquidity and risk.", "Complete investor onboarding and reporting."),
        "SEBI", AIF_2026, "14-07-2026",
        "AIFs are not equivalent to mutual funds and have different eligibility/risk structures."),
    RegulationTopic(
        "crypto_india_status", "Crypto / VDA regulatory position in India", "Crypto Regulation",
        "As of the March 2026 Lok Sabha answer used by FinAI, VDA service providers are brought into the AML/CFT framework and registered as FIU-IND reporting entities. The Government explicitly states that this registration should not be treated as a general licence, approval or endorsement.",
        ("Check the VDA service provider's current FIU-IND reporting-entity status.", "Check the product and account restrictions for the specific platform.", "Complete KYC and keep transaction records.", "Track current tax/TDS and reporting obligations.", "Recheck current Government and FIU notifications before relying on the status."),
        "FIU-IND / Government of India", VDA_REGISTER, "09-03-2026 snapshot",
        "The official answer says there was no public list because publication could create a misleading impression of licence/endorsement."),
    ),
    RegulationTopic(
        "create_crypto_token", "How to create a cryptocurrency or token", "Crypto Mechanics",
        "Creating a cryptoasset can mean launching a native blockchain coin or deploying a token on an existing blockchain. The technical design and legal/compliance analysis are separate layers.",
        ("Choose native blockchain versus token on an existing chain.", "Define token supply, issuance, decimals, transfers, permissions and governance.", "Implement consensus/network infrastructure for a native chain or audited smart contracts for a token.", "Test security, key management and upgrade controls.", "Design custody, treasury, disclosures and incident response.", "Obtain jurisdiction-specific legal/tax/compliance advice before offering, marketing or facilitating the asset."),
        "Technical architecture + applicable jurisdictional law", "https://fiuindia.gov.in/files/downloads/downloads.html", "Current framework",
        "Technical ability to deploy a token does not by itself establish that its issuance, sale, exchange or promotion is lawful or regulated."),
    ),
    RegulationTopic(
        "mining_economics", "Proof-of-work mining economics", "Crypto Mechanics",
        "Mining profitability depends on block subsidy and transaction fees, network difficulty/hash rate, your hash rate, pool fees, hardware efficiency, electricity price, uptime and the market price of the mined asset.",
        ("Measure hardware hash rate and electrical power.", "Use current network difficulty/hash-rate and block-reward data.", "Estimate expected coin production from network share.", "Subtract pool fees, electricity, hardware depreciation and other costs.", "Stress-test the economics against price, difficulty and uptime changes."),
        "Network/protocol data + miner/pool disclosures", "https://developer.bitcoin.org/reference/rpc/getmininginfo.html", "Dynamic",
        "A profitability result is a scenario, not a guarantee; network conditions change continuously."),
    ),
)


def list_regulations(category: Optional[str] = None) -> List[Dict[str, object]]:
    items = TOPICS
    if category:
        c = category.strip().lower()
        items = tuple(item for item in items if item.category.lower() == c)
    return [asdict(item) for item in items]


def search_regulations(query: str) -> List[Dict[str, object]]:
    q = " ".join(str(query).strip().lower().split())
    if not q:
        return []
    results = []
    for item in TOPICS:
        haystack = " ".join([
            item.topic_id, item.title, item.category, item.answer,
            " ".join(item.steps),
        ]).lower()
        if q in haystack or any(token in haystack for token in q.split()):
            results.append(asdict(item))
    return results[:25]
