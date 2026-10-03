"""Resident-vs-NRI investment route matrix for India.

This catalog is intentionally source-linked and conservative: "permitted" means
generally permitted subject to the stated FEMA/SEBI/tax/security conditions,
not an unconditional permission for every transaction.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class InvestmentRoute:
    route_id: str
    category: str
    avenue: str
    resident_status: str
    nri_status: str
    resident_route: str
    nri_route: str
    key_conditions: Tuple[str, ...]
    authority: str
    official_source: str
    as_of: str
    accuracy_note: str


RBI_LRS = "https://www.rbi.org.in/scripts/notificationuser.aspx?id=10192"
RBI_OI = "https://www.rbi.org.in/Scripts/BS_ViewMasterDirections.aspx?id=10192"
RBI_NRI = "https://rbi.org.in/SCRIPTS/BS_FemaNotifications.aspx?Id=11723"
RBI_DEPOSITS = "https://www.rbi.org.in/Scripts/BS_ViewMasCirculardetails.aspx?id=8096"
RBI_PROPERTY = "https://www.rbi.org.in/CommonPerson/english/Scripts/Notification.aspx?Id=730"
SEBI_REGS = "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListingLegal=yes&sid=1&smid=0&ssid=3"
SEBI_FPI = "https://www.sebi.gov.in/legal/regulations/jul-2026/securities-and-exchange-board-of-india-foreign-portfolio-investors-regulations-2019-last-amended-on-july-07-2026-_102902.html"
PFRDA_NPS = "https://www.pfrda.org.in/en/schemes/national-pension-system/nps-for-all-citizen-models"
DEA_SMALL = "https://dea.gov.in/budget-division/475"
RBI_SGB = "https://sovereigngoldbonds.rbi.org.in/"
INCOME_TAX = "https://www.incometax.gov.in/iec/foportal/"

ROUTES = (
    InvestmentRoute(
        "listed_equity", "Equity", "Listed equity shares",
        "Generally permitted",
        "Permitted subject to FEMA/NDI/NRI rules and route/sector limits",
        "Regular demat + broker/exchange account",
        "NRI/OCI investment under applicable repatriation/non-repatriation framework; PIS may apply for specified secondary-market transactions",
        ("KYC/demat", "sectoral/aggregate foreign investment limits where applicable",
         "pricing/reporting for foreign investment where applicable"),
        "SEBI / RBI / FEMA", SEBI_REGS, "2026",
        "NRI treatment depends on the security and repatriation basis; do not treat the resident rules as identical.",
    ),
    InvestmentRoute(
        "equity_derivatives", "Equity Derivatives", "Exchange-traded equity futures/options",
        "Generally permitted subject to exchange/broker/risk rules",
        "Permitted subject to applicable NRI position limits and market/FEMA rules",
        "SEBI-registered broker and exchange derivatives account",
        "Eligible NRIs may access exchange-traded equity derivatives subject to applicable limits and requirements",
        ("Margin rules", "position limits", "broker eligibility", "FEMA restrictions"),
        "SEBI / RBI", SEBI_REGS, "2026",
        "The blanket claim that NRIs cannot trade all equity derivatives is inaccurate; SEBI publishes NRI derivative participation rules.",
    ),
    InvestmentRoute(
        "short_selling", "Equity Trading", "Short selling",
        "Permitted within the applicable short-selling framework",
        "Not permitted for NRI portfolio investment in the cited RBI NRI framework; delivery requirements apply",
        "Exchange short-sale rules and securities-lending framework",
        "NRI PIS activity must comply with delivery/short-selling restrictions",
        ("Security-specific rules", "broker controls", "securities lending where applicable"),
        "SEBI / RBI", RBI_NRI, "Current framework",
        "The restriction is specific to the NRI investment framework; it should not be generalized to every non-resident trading route.",
    ),
    InvestmentRoute(
        "ipo", "Primary Markets", "IPO / public issue",
        "Permitted",
        "Permitted subject to issue terms, FEMA/SEBI conditions and investor status",
        "Apply through eligible broker/bank/issue mechanism",
        "Use the route allowed for the investor's status and the particular issue",
        ("Issue eligibility", "KYC", "foreign investment limits", "issue-specific documentation"),
        "SEBI / RBI", SEBI_REGS, "2026",
        "IPO participation can differ by investor class and issue structure.",
    ),
    InvestmentRoute(
        "etf", "Funds", "Exchange-traded funds",
        "Permitted",
        "Permitted subject to the applicable FEMA/SEBI route",
        "Demat + exchange/broker",
        "NRI purchase/sale follows applicable foreign investment and repatriation conditions",
        ("ETF scheme terms", "KYC", "foreign investment conditions", "tax"),
        "SEBI / RBI", SEBI_REGS, "2026",
        "Specific ETF eligibility and tax treatment should be checked from the scheme and current law.",
    ),
    InvestmentRoute(
        "mutual_fund", "Funds", "Domestic mutual funds",
        "Permitted",
        "Permitted subject to FEMA/account/repatriation and scheme onboarding requirements",
        "AMC/regulated platform",
        "Investment can be funded through permitted NRE/FCNR/NRO/inward-remittance routes depending on repatriation basis",
        ("KYC", "FATCA/CRS where applicable", "repatriation basis", "scheme acceptance"),
        "SEBI / RBI", RBI_NRI, "2026",
        "US/Canada investor restrictions are often fund/AMC-specific and should not be treated as a universal statutory ban.",
    ),
    InvestmentRoute(
        "pms", "Managed Investments", "Portfolio Management Services",
        "Permitted subject to PMS onboarding",
        "Can be available subject to FEMA and PMS eligibility",
        "SEBI-registered portfolio manager",
        "Non-resident clients use the applicable FEMA and account route",
        ("Minimum investment rules", "KYC", "mandate", "tax"),
        "SEBI", SEBI_REGS, "2026",
        "The general PMS minimum investment is ₹50 lakh for new/fresh investments, subject to the accredited-investor exception.",
    ),
    InvestmentRoute(
        "aif", "Alternative Investments", "Alternative Investment Funds",
        "Permitted subject to investor eligibility",
        "Can be available subject to FEMA/SEBI conditions",
        "SEBI-regulated AIF onboarding",
        "Foreign investment route and fund documents determine eligibility",
        ("AIF category", "minimum ticket", "PPM", "KYC", "FEMA"),
        "SEBI / RBI", SEBI_REGS, "2026",
        "The general AIF minimum investment is ₹1 crore, with specified exceptions including accredited-investor treatment.",
    ),
    InvestmentRoute(
        "bank_fd", "Deposits", "Bank fixed deposits",
        "Permitted",
        "Permitted through resident/NRE/NRO/FCNR structures as applicable",
        "Resident bank FD",
        "NRE/FCNR/NRO deposit rules apply according to account status",
        ("tenure", "interest", "TDS/tax", "account type"),
        "RBI", RBI_DEPOSITS, "Current framework",
        "Tax treatment depends on account type and the holder's tax status.",
    ),
    InvestmentRoute(
        "nre", "Deposits", "NRE account",
        "Not applicable as a resident account",
        "Available to eligible non-residents",
        "Not applicable",
        "Foreign inward remittance / permitted credits under NRE rules; balances are generally repatriable",
        ("Eligibility", "permitted credits", "repatriation", "tax law"),
        "RBI", RBI_DEPOSITS, "Current framework",
        "NRE is a banking status rather than an investment product by itself.",
    ),
    InvestmentRoute(
        "nro", "Deposits", "NRO account",
        "Not applicable as an NRI account",
        "Available to persons resident outside India",
        "Not applicable",
        "Rupee account for bona fide India transactions; NRO balances are generally subject to a USD 1 million annual remittance facility under conditions",
        ("taxes", "bank satisfaction", "documentation", "repatriation limits"),
        "RBI", RBI_DEPOSITS, "Current framework",
        "The USD 1 million facility is not a blanket unrestricted withdrawal promise.",
    ),
    InvestmentRoute(
        "fcnr", "Deposits", "FCNR(B) deposits",
        "Not applicable as a non-resident deposit product",
        "Available to eligible NRIs/PIOs in permitted foreign currencies",
        "Not applicable",
        "Term deposit in permitted foreign currency",
        ("eligible currency", "tenure", "bank rules", "tax"),
        "RBI", RBI_DEPOSITS, "Current framework",
        "FCNR(B) is distinct from NRE/NRO and has its own rules.",
    ),
    InvestmentRoute(
        "gsecs", "Fixed Income", "Government securities / T-bills",
        "Permitted",
        "Permitted subject to FEMA investor route and security-specific rules",
        "RBI Retail Direct / eligible broker or bank",
        "NRIs may acquire specified government securities and T-bills under applicable repatriation/non-repatriation schedules",
        ("security type", "account/route", "repatriation", "market access"),
        "RBI / Government", RBI_NRI, "2026",
        "Specific limits and repatriation rules vary by instrument and route.",
    ),
    InvestmentRoute(
        "sgb", "Gold", "Sovereign Gold Bonds",
        "Available when fresh issuance is notified; existing bonds can trade/are redeemable under scheme rules",
        "Fresh primary subscription is restricted by the SGB scheme's resident-investor eligibility; non-resident holding can arise in specified transfer/nominee circumstances",
        "Fresh issues only when a Government-notified tranche is open; secondary market subject to trading rules",
        "Existing holdings and transfer/nominee cases follow the SGB scheme and FEMA rules",
        ("current issuance calendar", "eligibility", "secondary-market liquidity", "tax"),
        "RBI / Government", RBI_SGB, "2026",
        "As of the current RBI SGB page, recent public issue notifications shown are older while 2026 entries include redemption notices; FinAI must not label SGB as continuously open for subscription.",
    ),
    InvestmentRoute(
        "ppf", "Small Savings", "Public Provident Fund",
        "Permitted for eligible resident individuals",
        "New PPF accounts are not available to NRIs",
        "PPF account subject to scheme rules",
        "An account opened while resident can continue during the permitted maturity period on non-repatriation basis; current official material must be checked for the exact case",
        ("residential status", "maturity", "subscription limits", "scheme rules"),
        "DEA / National Savings Institute", DEA_SMALL, "2026",
        "The 2018 DEA memorandum kept the proposed automatic closure of existing PPF accounts on becoming non-resident in abeyance; current case handling should be checked against the latest scheme instructions.",
    ),
    InvestmentRoute(
        "small_savings", "Small Savings", "NSC / KVP / SCSS / SSA / MIS / Post Office schemes",
        "Available subject to each scheme's eligibility",
        "Generally not available to NRIs under the small-savings eligibility framework",
        "Post Office/bank channels under each scheme",
        "NRI eligibility differs from resident eligibility; do not assume a resident scheme is open to NRIs",
        ("scheme-specific eligibility", "age/status where applicable", "current rate", "tax"),
        "DEA / Department of Posts", DEA_SMALL, "2026",
        "FinAI should check the individual scheme's current rules rather than infer eligibility from a generic 'Post Office' label.",
    ),
    InvestmentRoute(
        "nps", "Retirement", "National Pension System",
        "Permitted",
        "Permitted for eligible Indian citizens and OCIs aged 18–85 under PFRDA's All Citizen Model",
        "PFRDA NPS onboarding",
        "Non-resident/OCI subscriber uses the NPS process and KYC requirements",
        ("age", "citizenship/status", "KYC", "withdrawal/exit rules"),
        "PFRDA", PFRDA_NPS, "2026",
        "PFRDA explicitly includes resident and non-resident Indian citizens and OCI in the All Citizen Model.",
    ),
    InvestmentRoute(
        "real_estate", "Real Estate", "Residential/commercial property in India",
        "Permitted subject to land/property law",
        "Permitted for residential/commercial property under FEMA; agricultural land/plantation/farmhouse purchase is restricted",
        "Domestic property purchase under applicable law",
        "NRI purchase through permitted banking channels and FEMA conditions",
        ("state land laws", "FEMA", "payment route", "registration/tax"),
        "RBI / State authorities", RBI_PROPERTY, "Current framework",
        "Resident land ownership is also subject to state-specific land and agricultural restrictions; 'all property without restrictions' is too broad.",
    ),
    InvestmentRoute(
        "reit_invit", "Alternatives", "REITs and InvITs",
        "Permitted",
        "Permitted subject to FEMA/SEBI investor and instrument rules",
        "Broker/exchange or eligible fund route",
        "NRI participation depends on the applicable foreign-investment/security framework",
        ("instrument rules", "KYC", "FEMA", "tax"),
        "SEBI / RBI", SEBI_REGS, "2026",
        "Treat REIT/InvIT access as framework-dependent rather than an unconditional permission.",
    ),
    InvestmentRoute(
        "overseas_portfolio", "Overseas", "Foreign listed securities / ETFs",
        "Permitted under LRS/OI framework",
        "Not an India-FEMA restriction on an NRI investing from overseas earnings outside India",
        "Resident individual uses LRS and applicable Overseas Investment rules",
        "NRI's overseas investments are generally governed by the residence country's law, plus tax and any Indian-source issues; Indian FEMA rules apply to India-facing transactions",
        ("LRS limit", "OI rules", "host-country law", "tax reporting"),
        "RBI / FEMA", RBI_LRS, "2026",
        "The USD 250,000 LRS ceiling applies to remittances by resident individuals and includes permitted current/capital transactions.",
    ),
    InvestmentRoute(
        "overseas_property", "Overseas", "Overseas immovable property",
        "Potentially permitted under LRS/OI rules, subject to conditions",
        "No Indian FEMA restriction simply because the person is an NRI investing outside India, but local-country law/tax applies",
        "Resident individual uses the current LRS/OI framework",
        "NRI uses residence/jurisdiction rules for foreign assets",
        ("LRS", "OI rules", "host-country law", "tax"),
        "RBI", RBI_LRS, "2026",
        "Do not treat LRS as permission for every foreign investment product; prohibited transactions and margin remittances remain outside the scheme.",
    ),
    InvestmentRoute(
        "overseas_direct", "Overseas", "Overseas direct investment / startup participation",
        "Permitted only under the Overseas Investment framework and applicable categories",
        "Generally outside the resident-LRS rule when made from overseas earnings, but India-source funds/residential status can alter the analysis",
        "Resident individual follows OI Rules/Regulations and reporting",
        "NRI uses the relevant host-country and Indian remittance/tax framework",
        ("OI classification", "reporting", "LRS where applicable", "sector/financial-services restrictions"),
        "RBI", RBI_OI, "2026",
        "ODI and OPI are distinct categories and should not be collapsed into 'buy any foreign startup'.",
    ),
)


def list_investment_routes(category: str | None = None) -> List[Dict[str, object]]:
    items = ROUTES
    if category:
        c = category.strip().lower()
        items = tuple(item for item in items if item.category.lower() == c)
    return [asdict(item) for item in items]


def search_investment_routes(query: str) -> List[Dict[str, object]]:
    q = " ".join(str(query).strip().lower().split())
    if not q:
        return []
    tokens = [token for token in q.split() if len(token) >= 3]
    scored = []
    for item in ROUTES:
        searchable = " ".join((item.route_id, item.category, item.avenue, item.resident_status, item.nri_status, *item.key_conditions)).lower()
        score = (12 if q in searchable else 0) + sum(2 for token in tokens if token in searchable)
        if score:
            scored.append((score, item))
    scored.sort(key=lambda pair: (-pair[0], pair[1].route_id))
    return [asdict(item) for _, item in scored[:25]]
