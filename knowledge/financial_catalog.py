from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class FinancialKnowledgeEntry:
    topic_id: str
    title: str
    category: str
    aliases: Tuple[str, ...]
    summary: str
    key_points: Tuple[str, ...]
    caveat: str


ENTRIES = (
    FinancialKnowledgeEntry(
        "investing_basics",
        "Investing Basics",
        "investments",
        ("investment", "investments", "investing", "invest"),
        "Investing means committing money or other capital to assets or activities with the objective of generating a return, while accepting some level of risk.",
        (
            "Different assets have different return, risk, liquidity and time-horizon characteristics.",
            "Diversification can reduce concentration risk but cannot remove investment risk.",
            "A financial goal and time horizon should be considered before selecting an investment product.",
        ),
        "Product suitability, taxation, charges and current rules depend on the specific investment and investor circumstances.",
    ),
    FinancialKnowledgeEntry(
        "mutual_funds",
        "Mutual Funds",
        "investments",
        ("mutual fund", "mutual funds", "mf"),
        "A mutual fund pools money from multiple investors and invests it in a portfolio managed according to the fund's stated mandate.",
        (
            "Returns are not guaranteed for market-linked funds.",
            "Different categories have different risk, liquidity and cost characteristics.",
            "Past performance does not guarantee future performance.",
        ),
        "For a specific fund, current NAV, portfolio, expense ratio and risk disclosures should come from current issuer and regulator documents.",
    ),
    FinancialKnowledgeEntry(
        "sip",
        "Systematic Investment Plan (SIP)",
        "investments",
        ("sip", "systematic investment plan", "systematic investment"),
        "A SIP is a recurring investment method, commonly used with mutual funds, where a fixed amount is invested at a chosen interval.",
        (
            "A SIP is a method of investing, not a separate asset class.",
            "The contribution amount and frequency can be changed subject to product and provider rules.",
            "Market-linked outcomes vary over time.",
        ),
        "Projected SIP values are illustrations, not guaranteed returns.",
    ),
    FinancialKnowledgeEntry(
        "bonds",
        "Bonds",
        "investments",
        ("bond", "bonds", "fixed income"),
        "A bond is a debt instrument through which an issuer borrows money and generally promises interest payments plus repayment of principal according to its terms.",
        (
            "Credit risk depends on the issuer.",
            "Bond prices can move when market interest rates change.",
            "Maturity, coupon, yield and duration are different concepts.",
        ),
        "Actual coupon, yield, rating, liquidity and redemption terms depend on the specific issue.",
    ),
    FinancialKnowledgeEntry(
        "money_market",
        "Money Market",
        "investments",
        ("money market", "money markets"),
        "The money market covers short-term borrowing and lending instruments used for liquidity and short-duration financing.",
        (
            "Examples can include Treasury bills and other short-term debt instruments.",
            "Credit, liquidity and interest-rate risks vary by instrument.",
            "Money-market is a broad category, not one uniform product.",
        ),
        "Current eligibility, yields and availability depend on the specific instrument and market conditions.",
    ),
    FinancialKnowledgeEntry(
        "fixed_deposit",
        "Fixed Deposit (FD)",
        "deposits",
        ("fixed deposit", "fixed deposits", "fd", "fds"),
        "A fixed deposit is a deposit arrangement in which money is placed with a bank or other eligible institution for a stated term at specified interest terms.",
        (
            "Maturity depends on principal, rate, tenure and compounding rules.",
            "Premature withdrawal rules and penalties depend on the provider.",
            "Deposit protection and applicable limits depend on the institution and current rules.",
        ),
        "Use the current institution's rate sheet and terms for a real FD decision.",
    ),
    FinancialKnowledgeEntry(
        "recurring_deposit",
        "Recurring Deposit (RD)",
        "deposits",
        ("recurring deposit", "recurring deposits", "rd", "rds"),
        "A recurring deposit is a deposit product in which a customer makes regular deposits over a specified tenure and earns interest under the provider's terms.",
        (
            "The regular contribution is fixed for the agreed schedule.",
            "Interest and maturity calculation depend on provider rules.",
            "Delayed instalments can attract charges under product terms.",
        ),
        "Rates, minimum instalments and penalties vary by provider.",
    ),
    FinancialKnowledgeEntry(
        "ppf",
        "Public Provident Fund (PPF)",
        "government_savings",
        ("ppf", "public provident fund"),
        "PPF is a long-term government-backed small-savings product with defined contribution, interest, withdrawal and maturity rules.",
        (
            "It is designed for long-term savings.",
            "Contribution limits and tax treatment are governed by current rules.",
            "Withdrawals and loans are subject to product conditions.",
        ),
        "Current interest rates, limits and tax rules must be checked against the latest official notification.",
    ),
    FinancialKnowledgeEntry(
        "nsc",
        "National Savings Certificate (NSC)",
        "government_savings",
        ("nsc", "national savings certificate"),
        "NSC is a government small-savings product with a specified tenure and interest mechanism.",
        (
            "It is a savings/investment product rather than a market-traded equity instrument.",
            "Interest and tax treatment follow applicable rules.",
            "Premature encashment is subject to defined conditions.",
        ),
        "Current rates and tax treatment should be checked against the latest official source.",
    ),
    FinancialKnowledgeEntry(
        "scss",
        "Senior Citizens' Savings Scheme (SCSS)",
        "government_savings",
        ("scss", "senior citizens savings scheme"),
        "SCSS is a government small-savings scheme designed for eligible senior citizens, with defined deposit, interest and withdrawal rules.",
        (
            "Eligibility and age conditions apply.",
            "Interest is paid according to the scheme schedule.",
            "Premature closure is subject to conditions.",
        ),
        "Current eligibility, rates and limits must be verified from the latest official source.",
    ),
    FinancialKnowledgeEntry(
        "post_office_savings",
        "Post Office Small-Savings",
        "government_savings",
        ("post office", "post office scheme", "post office schemes", "small savings"),
        "Post Office small-savings products are government-administered savings schemes with different tenures, contribution rules and payout structures.",
        (
            "Different schemes serve different goals and eligibility groups.",
            "Examples include PPF, NSC and SCSS.",
            "Each scheme has its own current rate, limit, maturity and withdrawal rules.",
        ),
        "Treat rates and eligibility as time-sensitive and verify them from current official notifications.",
    ),
    FinancialKnowledgeEntry(
        "crypto",
        "Cryptocurrency",
        "digital_assets",
        ("crypto", "cryptocurrency", "cryptocurrencies", "bitcoin", "ethereum"),
        "Cryptocurrency refers to digital assets that use cryptographic techniques and distributed-ledger systems; prices can be highly volatile.",
        (
            "Crypto assets can have substantial price volatility.",
            "Operational, custody, technology and regulatory risks may apply.",
            "Different tokens can have very different designs and risk profiles.",
        ),
        "Applicable tax, regulatory and platform rules can change; verify current rules before acting.",
    ),
    FinancialKnowledgeEntry(
        "etf",
        "Exchange-Traded Fund (ETF)",
        "investments",
        ("etf", "etfs", "exchange traded fund", "exchange-traded fund"),
        "An ETF is a pooled investment vehicle whose units trade on an exchange during market hours, subject to the fund's structure and rules.",
        (
            "ETF prices can move during the trading day.",
            "Some ETFs track an index or asset class.",
            "Brokerage, spread, tracking difference and fund costs can matter.",
        ),
        "Review current scheme information and exchange data for a specific ETF.",
    ),
    FinancialKnowledgeEntry(
        "gold",
        "Gold",
        "asset_class",
        ("gold investment", "gold", "gold price"),
        "Gold is an asset class commonly used for diversification and as exposure to the price of the metal.",
        (
            "Gold can be accessed through physical gold and financial products.",
            "Returns depend on the chosen form of exposure and its costs.",
            "Gold does not represent an operating company's cash flow or earnings.",
        ),
        "Product-specific costs, taxation and liquidity depend on the chosen gold instrument.",
    ),
    FinancialKnowledgeEntry(
        "inflation",
        "Inflation",
        "economics",
        ("inflation", "price inflation"),
        "Inflation is a sustained increase in the general level of prices, which reduces the purchasing power of a currency over time.",
        (
            "Inflation is measured with price indices rather than the price of one product alone.",
            "Different households and sectors can experience different effective inflation.",
            "Investment returns should be considered relative to inflation for long-term goals.",
        ),
        "Use current official inflation data for a time-specific comparison.",
    ),
    FinancialKnowledgeEntry(
        "cagr",
        "Compound Annual Growth Rate (CAGR)",
        "calculations",
        ("cagr", "compound annual growth rate"),
        "CAGR is a standardized way to express the annualized growth rate of an investment over a period when only beginning and ending values are considered.",
        (
            "CAGR is an annualized rate, not a statement that the investment grew at that exact rate every year.",
            "It does not capture interim cash flows.",
            "IRR/XIRR may be more appropriate when contributions or withdrawals occur at different times.",
        ),
        "Use the exact dates and cash flows when calculating an investment return.",
    ),
    FinancialKnowledgeEntry(
        "diversification",
        "Diversification",
        "portfolio",
        ("diversification", "diversify", "diversified"),
        "Diversification means spreading exposure across investments or risk sources so that one concentration does not dominate the portfolio.",
        (
            "Diversification can reduce concentration risk.",
            "It cannot eliminate market or systemic risk.",
            "Diversification should be evaluated alongside goals, time horizon and liquidity.",
        ),
        "The degree of diversification should be measured using actual portfolio holdings and exposures.",
    ),
    FinancialKnowledgeEntry(
        "market_cap",
        "Market Capitalization",
        "markets",
        ("market cap", "market capitalization"),
        "Market capitalization is the market value of a company's outstanding equity, commonly calculated as share price multiplied by shares outstanding.",
        (
            "Market cap is a valuation measure, not the same as enterprise value.",
            "It changes as share price and share count change.",
            "Market-cap classifications can differ by methodology and market.",
        ),
        "For a specific company, use current exchange/company data.",
    ),
    FinancialKnowledgeEntry(
        "pe_ratio",
        "Price-to-Earnings Ratio (P/E)",
        "markets",
        ("p/e", "pe ratio", "price to earnings", "price earnings ratio"),
        "The P/E ratio relates a company's market price to its earnings per share and is commonly used as one valuation measure.",
        (
            "A high or low P/E cannot be interpreted without context.",
            "Cyclicality, accounting choices and negative earnings can affect usefulness.",
            "Peer, sector and historical comparisons can provide context.",
        ),
        "Use current financial statements and comparable companies for a current valuation analysis.",
    ),
    FinancialKnowledgeEntry(
        "ipo",
        "Initial Public Offering (IPO)",
        "markets",
        ("ipo", "initial public offering", "public issue"),
        "An IPO is a public offering through which a company offers securities to public investors as it becomes publicly traded, subject to the applicable market process.",
        (
            "IPO pricing and allocation are governed by the issue process.",
            "An IPO investment carries market and company-specific risks.",
            "The prospectus contains the offer-specific business, financial and risk information.",
        ),
        "Use the current issue documents and exchange/regulator disclosures for a live IPO.",
    ),
    FinancialKnowledgeEntry(
        "insurance",
        "Insurance",
        "personal_finance",
        ("insurance", "life insurance", "health insurance", "general insurance"),
        "Insurance is a risk-transfer arrangement under which a policyholder pays a premium for specified coverage subject to the policy terms.",
        (
            "Coverage, exclusions, deductibles and limits matter as much as premium.",
            "Policy terms differ across products.",
            "Insurance is primarily about risk protection rather than a universal investment substitute.",
        ),
        "Use the current policy wording and insurer disclosures for a specific product.",
    ),
    FinancialKnowledgeEntry(
        "credit_score",
        "Credit Score",
        "personal_finance",
        ("credit score", "credit rating personal"),
        "A personal credit score is a numerical summary derived from credit-history information using the scoring methodology of the relevant bureau.",
        (
            "Payment history and credit utilization can affect scores under the scoring model.",
            "Different bureaus and scoring models can produce different values.",
            "A credit score is not itself a loan approval guarantee.",
        ),
        "For an actual score or lender decision, use current bureau and lender information.",
    ),
    FinancialKnowledgeEntry(
        "portfolio",
        "Investment Portfolio",
        "portfolio",
        ("portfolio", "investment portfolio"),
        "A portfolio is the collection of investments held by an investor, evaluated together for return, risk, liquidity and diversification.",
        (
            "Asset allocation distributes capital across asset classes.",
            "Diversification can reduce concentration risk but cannot eliminate investment risk.",
            "Portfolio performance should be considered alongside risk and time horizon.",
        ),
        "A suitable portfolio depends on goals, time horizon, risk tolerance and constraints.",
    ),
)


def _normalize(text: str) -> str:
    return " ".join(str(text).strip().lower().split())


def find_entries(query: str, limit: int = 3) -> Tuple[FinancialKnowledgeEntry, ...]:
    normalized = _normalize(query)
    if not normalized:
        return ()

    tokens = set(normalized.replace("/", " ").replace("-", " ").split())
    scored = []

    for entry in ENTRIES:
        alias_tokens = set()
        for alias in entry.aliases:
            alias_tokens.update(
                _normalize(alias).replace("/", " ").replace("-", " ").split()
            )

        score = 0
        if any(alias in normalized for alias in entry.aliases):
            score += 6
        score += len(tokens & alias_tokens) * 2

        if entry.category.replace("_", " ") in normalized:
            score += 1

        if score:
            scored.append((score, entry))

    scored.sort(key=lambda item: (-item[0], item[1].topic_id))
    return tuple(entry for _, entry in scored[: max(1, int(limit))])


def build_answer(query: str, limit: int = 3) -> dict:
    matches = find_entries(query, limit=limit)

    if not matches:
        return {"found": False, "matches": [], "answer": ""}

    primary = matches[0]
    sections = [primary.title, primary.summary, "", "Key points:"]
    sections.extend(f"- {point}" for point in primary.key_points)

    if len(matches) > 1:
        sections.extend(["", "Related topics:"])
        sections.extend(
            f"- {entry.title}: {entry.summary}"
            for entry in matches[1:]
        )

    sections.extend(["", f"Data note: {primary.caveat}"])

    return {
        "found": True,
        "matches": [
            {
                "topic_id": entry.topic_id,
                "title": entry.title,
                "category": entry.category,
            }
            for entry in matches
        ],
        "answer": "\n".join(sections),
    }
