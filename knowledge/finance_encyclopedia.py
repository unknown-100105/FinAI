"""Broad finance, money, markets and crypto mechanics knowledge.

Static concepts are intentionally separated from current data. Current prices,
rates, laws, eligibility, filings and regulatory status must be retrieved from
current official/provider sources.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Tuple


@dataclass(frozen=True)
class FinanceTopic:
    topic_id: str
    title: str
    category: str
    aliases: Tuple[str, ...]
    what_it_is: str
    how_it_works: Tuple[str, ...]
    why_it_matters: str
    current_data_needed: bool = False
    source_hint: str = ""


def T(topic_id: str, title: str, category: str, aliases: Tuple[str, ...],
      what: str, how: Tuple[str, ...], why: str,
      current: bool = False, source: str = "") -> FinanceTopic:
    return FinanceTopic(topic_id, title, category, aliases, what, how, why, current, source)


TOPICS = (
    T("money", "Money", "foundations", ("money", "currency"),
      "Money functions as a medium of exchange, unit of account and store of value.",
      ("People accept money because it is widely transferable and usable for settlement.", "Bank deposits and physical cash are different forms of money.", "Inflation changes purchasing power over time."),
      "Money is the base layer connecting prices, saving, credit and payments."),
    T("history_money", "History of Money", "history", ("history of money", "money history", "evolution of money"),
      "The history of money runs from commodity exchange and coinage to banknotes, deposits and digital payment systems.",
      ("Coinage standardized units of value.", "Banknotes and bank deposits made monetary claims easier to transfer.", "Central banking and fiat systems became dominant in modern economies.", "Electronic payments moved settlement into account-based networks.", "Crypto introduced permissionless digital assets."),
      "Historical context explains why modern money and payment systems work differently."),
    T("history_finance", "History of Finance", "history", ("history of finance", "financial history"),
      "Financial history traces the development of lending, insurance, public debt, joint-stock companies, exchanges, banking, central banking and electronic markets.",
      ("Credit developed alongside trade.", "Public debt expanded state financing.", "Joint-stock companies pooled investor capital.", "Organized exchanges enabled secondary-market price discovery.", "Modern finance increasingly uses electronic and programmable infrastructure."),
      "Finance today is the result of centuries of institutional and technological evolution."),
    T("banking", "Commercial Banking", "banking", ("bank", "banks", "banking"),
      "Commercial banks take deposits, provide credit and offer payment and financial services.",
      ("Deposits are bank liabilities.", "Loans are bank assets.", "Interest and fees generate bank income.", "Capital, liquidity and risk rules constrain balance-sheet activity."),
      "Banks connect savers, borrowers and payment systems."),
    T("central_bank", "Central Banking", "monetary_system", ("central bank", "central banking"),
      "A central bank performs monetary and financial-system functions under its legal mandate.",
      ("Policy rates influence short-term financial conditions.", "Liquidity operations affect money-market funding.", "Policy transmits through lending, deposits, exchange rates and asset prices."),
      "Central banks are a key link between monetary conditions and the economy.", True, "RBI or the relevant national central bank."),
    T("fiat", "Fiat Money", "monetary_system", ("fiat money", "fiat currency"),
      "Fiat money is not redeemable for a fixed quantity of a commodity and operates within a monetary and legal system.",
      ("Its purchasing power changes with inflation.", "Its supply is influenced by monetary and banking institutions.", "Interest rates affect demand for money and credit."),
      "Most modern national currencies use fiat monetary systems."),
    T("inflation", "Inflation", "economics", ("inflation", "price inflation"),
      "Inflation is a sustained increase in the general price level.",
      ("Price indices measure changes in representative baskets.", "Inflation reduces the real purchasing power of fixed nominal amounts.", "Nominal investment returns can be adjusted for inflation to examine real returns."),
      "Inflation affects savings, debt, wages and investment goals.", True, "Current official CPI and monetary-policy data."),
    T("monetary_policy", "Monetary Policy", "economics", ("monetary policy", "interest rate policy"),
      "Monetary policy changes financial conditions to influence inflation and economic activity.",
      ("Policy rates affect short-term borrowing costs.", "Liquidity operations influence money-market conditions.", "Financial conditions transmit to consumption, investment and asset prices."),
      "It is a major mechanism linking the central bank to markets.", True, "RBI monetary-policy publications."),
    T("stocks", "Stocks / Equities", "markets", ("stock", "stocks", "equity", "share", "shares"),
      "A stock represents an ownership interest in a company.",
      ("Shares trade through bids and offers.", "Prices change as market participants update expectations.", "Returns can come from price appreciation and dividends."),
      "Equities provide ownership exposure to businesses.", True, "Current exchange and issuer data."),
    T("ipo", "Initial Public Offering", "capital_markets", ("ipo", "initial public offering"),
      "An IPO is a public offering through which eligible securities can be offered and become publicly traded.",
      ("Eligibility is assessed under the applicable framework.", "Intermediaries conduct due diligence and prepare disclosures.", "Investors subscribe under the issue process.", "Allocation is followed by exchange listing and continuing obligations."),
      "IPOs connect corporate fundraising with public-market price discovery.", True, "SEBI ICDR and current exchange rules."),
    T("bond", "Bonds", "fixed_income", ("bond", "bonds", "fixed income"),
      "A bond is a debt instrument with contractual cash flows defined by its terms.",
      ("The issuer raises capital.", "The investor receives coupon and principal payments as specified.", "The security can trade before maturity.", "Credit, duration and liquidity affect value."),
      "Bonds finance governments and companies and provide fixed-income exposure."),
    T("bond_yield", "Bond Yield", "fixed_income", ("bond yield", "ytm", "yield to maturity", "yield"),
      "Bond yield relates a bond's price to its contractual cash flows under a stated convention.",
      ("For a conventional fixed-rate bond, a higher required yield generally means a lower price.", "Yield to maturity incorporates coupon payments and redemption under simplifying assumptions.", "Credit, liquidity and options affect market yields."),
      "Yield is fundamental to fixed-income valuation.", True, "Current government-securities and market data."),
    T("yield_curve", "Yield Curve", "fixed_income", ("yield curve", "term structure"),
      "A yield curve shows yields across maturities for a defined set of debt securities or reference rates.",
      ("Maturities can have different yields.", "Curve shape reflects expectations, term premium and market conditions.", "Curve movements change financing and valuation assumptions."),
      "The curve summarizes the time dimension of interest rates.", True, "RBI and government-securities data."),
    T("money_market", "Money Market", "money_market", ("money market", "money markets"),
      "The money market covers short-term borrowing, lending and liquidity instruments.",
      ("Overnight funding markets manage very short-term liquidity.", "Treasury bills provide short-duration government exposure.", "Repo and other instruments transfer liquidity against contractual terms."),
      "Money markets support daily funding and monetary-policy transmission.", True, "RBI money-market publications."),
    T("repo", "Repo", "money_market", ("repo", "repurchase agreement", "reverse repo"),
      "A repo is a financing transaction structured around the sale and repurchase of securities.",
      ("Cash is exchanged against securities.", "The securities are repurchased under agreed terms.", "Repo rates are important short-term funding prices."),
      "Repos provide collateralized liquidity and form an important money-market mechanism.", True, "RBI market-operations data."),
    T("treasury_bill", "Treasury Bills", "government_securities", ("treasury bill", "t-bill", "t bills"),
      "Treasury bills are short-term government securities with maturity and auction economics defined by the government-securities framework.",
      ("They are issued through auctions.", "Investors receive the applicable redemption value at maturity.", "The difference between acquisition economics and redemption contributes to return."),
      "T-bills are important short-term government funding instruments.", True, "RBI and Government of India auctions."),
    T("mutual_fund", "Mutual Funds", "investments", ("mutual fund", "mutual funds", "mf"),
      "A mutual fund pools investor money and invests it under a stated scheme mandate.",
      ("Investors receive units.", "The portfolio is managed according to scheme documents.", "NAV represents the scheme's valuation under applicable rules.", "Costs, risk, liquidity and tax treatment depend on the scheme and investor."),
      "Mutual funds provide pooled exposure across assets.", True, "SEBI scheme documents and current factsheets."),
    T("sip", "Systematic Investment Plan", "investments", ("sip", "systematic investment plan"),
      "A SIP is a recurring contribution method often used to invest in mutual funds.",
      ("A chosen amount is invested at scheduled intervals.", "The contribution buys units at the applicable NAV.", "Unit quantity changes when the price changes.", "Returns remain market-dependent."),
      "SIP automates recurring investing but does not guarantee a return."),
    T("etf", "Exchange-Traded Funds", "investments", ("etf", "etfs", "exchange traded fund"),
      "An ETF is a pooled investment product whose units trade on an exchange.",
      ("Orders trade during market hours.", "Market price can differ from NAV.", "Bid-ask spread and tracking difference affect realized outcomes."),
      "ETFs combine pooled exposure with exchange trading.", True, "SEBI ETF investor information and scheme documents."),
    T("derivatives", "Derivatives", "derivatives", ("derivative", "derivatives"),
      "A derivative derives its value from an underlying asset, index, rate or other reference.",
      ("Contracts define payoff and settlement.", "Participants use them for hedging or exposure.", "Margin and leverage can amplify outcomes."),
      "Derivatives transfer and reshape risk."),
    T("futures", "Futures", "derivatives", ("future", "futures", "futures contract"),
      "A futures contract standardizes an obligation linked to an underlying and settlement date.",
      ("Contracts specify expiry and size.", "Positions are generally margined and marked to market.", "Futures prices differ from spot due to carry and market conditions."),
      "Futures provide standardized leveraged exposure."),
    T("options", "Options", "derivatives", ("option", "options", "call", "put"),
      "An option gives the holder a right under specified contract terms, while the writer has the corresponding obligation.",
      ("The buyer pays a premium.", "Calls and puts have different payoff directions.", "Value depends on strike, time, volatility, underlying price and rates."),
      "Options create nonlinear payoff profiles."),
    T("order_book", "Order Book and Price Discovery", "markets", ("order book", "price discovery", "limit order", "market order"),
      "An order book records resting buy and sell orders.",
      ("The best bid is the highest displayed buy price.", "The best ask is the lowest displayed sell price.", "The spread is the gap between them.", "Compatible orders trade and update the book.", "Depth affects execution quality."),
      "The order book explains how quotes become transactions.", True, "Current exchange market data."),
    T("market_cap", "Market Capitalization", "valuation", ("market cap", "market capitalization"),
      "Market capitalization is commonly price multiplied by shares outstanding.",
      ("It changes with market price and share count.", "It measures equity size rather than total enterprise value."),
      "Market cap is a basic market-size measure.", True, "Current exchange/company data."),
    T("pe_ratio", "P/E Ratio", "valuation", ("p/e", "pe ratio", "price to earnings"),
      "P/E compares market price with earnings per share under a stated earnings basis.",
      ("It may be trailing or forward.", "Negative earnings can make the ratio unusable.", "Sector growth and cyclicality affect interpretation."),
      "P/E is one valuation measure among many."),
    T("payments", "Payments and Settlement", "payments", ("payments", "payment system", "settlement"),
      "Payment systems transfer value or the financial claims representing value.",
      ("Messaging and authorization are distinct from settlement.", "Banks or payment institutions may maintain underlying accounts.", "The payment rail determines settlement rules."),
      "Payments connect financial records with real-world commerce."),
    T("upi", "UPI", "payments", ("upi", "unified payments interface"),
      "UPI is an interoperable Indian retail payment system.",
      ("A payer initiates a payment request through a participating institution.", "The payment is routed across the participating ecosystem.", "Authorization and settlement follow scheme and bank processes."),
      "UPI demonstrates interoperable account-to-account retail payments.", True, "NPCI and participant-bank documentation."),
    T("rtgs", "RTGS", "payments", ("rtgs", "real time gross settlement"),
      "RTGS settles eligible transactions individually in real time under system rules.",
      ("Instructions are submitted through participating institutions.", "Transactions settle gross rather than as a net batch."),
      "RTGS illustrates central-bank settlement infrastructure.", True, "RBI RTGS information."),
    T("neft", "NEFT", "payments", ("neft", "national electronic funds transfer"),
      "NEFT is an electronic funds-transfer system operated under RBI rules.",
      ("Customers initiate transfers through participating institutions.", "The system processes the transfer according to its operating cycle and rules."),
      "NEFT is a major Indian account-to-account transfer rail.", True, "RBI NEFT information."),
    T("crypto", "Cryptocurrency", "digital_assets", ("crypto", "cryptocurrency", "cryptoasset", "vda"),
      "Cryptoassets are digital assets that use cryptographic techniques and may use distributed networks.",
      ("Transactions are authorized through cryptographic keys.", "Blockchain protocols maintain transaction state.", "Centralized and decentralized venues provide different market structures."),
      "Crypto combines software, market and custody risk.", True, "Current law, regulator and platform information."),
    T("bitcoin", "Bitcoin", "digital_assets", ("bitcoin", "btc"),
      "Bitcoin is a decentralized cryptoasset network using proof of work and a native asset.",
      ("Transactions are broadcast to the network.", "Miners compete using proof of work.", "Accepted blocks form the chain history.", "Private keys authorize spending."),
      "Bitcoin is a foundational permissionless digital-asset system.", True, "Bitcoin protocol documentation and live network data."),
    T("blockchain", "Blockchain", "digital_assets", ("blockchain", "distributed ledger", "dlt"),
      "A blockchain is a distributed ledger in which state changes are organized under a protocol's consensus rules.",
      ("Nodes receive transactions.", "Consensus determines accepted state.", "Cryptographic links connect block history.", "Different networks use different security and governance models."),
      "Blockchain is the infrastructure concept behind many digital assets and DLT applications."),
    T("hash", "Cryptographic Hash Functions", "cryptography", ("hash", "hash function", "cryptographic hash"),
      "A cryptographic hash maps input data to a fixed-size digest with properties useful for integrity and security.",
      ("The same input produces the same digest.", "Small input changes produce different digests with high probability.", "Blockchains use hashes to link and identify data.", "Proof-of-work uses repeated hashing."),
      "Hash functions are a core building block of modern digital-asset infrastructure."),
    T("pow", "Proof of Work", "digital_assets", ("proof of work", "pow"),
      "Proof of work is a consensus design that makes block production depend on computational work.",
      ("Miners search for a value satisfying a protocol condition.", "The network recognizes valid work under consensus rules.", "Attack cost is tied to computational resources."),
      "It links network security to computation and mining economics."),
    T("pos", "Proof of Stake", "digital_assets", ("proof of stake", "pos"),
      "Proof of stake links participation in consensus to staked economic value.",
      ("Validators lock or delegate stake.", "Protocol rules assign consensus duties.", "Penalties may apply to defined misbehavior."),
      "Proof of stake uses a different security and economic model from proof of work."),
    T("stablecoin", "Stablecoins", "digital_assets", ("stablecoin", "stablecoins"),
      "A stablecoin is a cryptoasset designed to target a relatively stable reference value.",
      ("Reserve-backed designs depend on reserves and redemption.", "Other designs use collateral or algorithmic mechanisms.", "De-pegging and counterparty risks differ by design."),
      "Stablecoins connect crypto market infrastructure with money-like settlement.", True, "Issuer disclosures and current regulatory treatment."),
    T("defi", "Decentralized Finance", "digital_assets", ("defi", "decentralized finance"),
      "DeFi refers to financial applications implemented with smart contracts and blockchain networks.",
      ("Users interact with programmable contracts.", "Lending, exchange and derivatives can be encoded on-chain.", "Oracle, smart-contract, liquidity and governance risks vary."),
      "DeFi demonstrates programmable financial-market functions."),
    T("wallet", "Crypto Wallets and Custody", "digital_assets", ("wallet", "crypto wallet", "self custody", "custody"),
      "A crypto wallet manages keys used to authorize transactions; the blockchain records asset state.",
      ("Self-custody leaves key control with the user.", "Custodial services hold keys on behalf of users.", "Loss or compromise of keys can affect access."),
      "Custody is an important operational risk."),
    T("smart_contract", "Smart Contracts", "digital_assets", ("smart contract", "smart contracts"),
      "A smart contract is executable software deployed to a blockchain environment.",
      ("Users call functions through transactions.", "The code changes on-chain state under defined rules.", "Access control and upgrade mechanisms determine who can modify behavior.", "Bugs can cause financial loss."),
      "Smart contracts make financial logic programmable."),
    T("token", "Crypto Tokens", "digital_assets", ("token", "tokens", "crypto token", "erc20", "erc-20"),
      "A token is a blockchain asset implemented through a native asset model or a token contract on an existing chain.",
      ("The design defines supply and transfer rules.", "Contracts can include permissions and governance.", "The host chain and contract add technical risks.", "Legal treatment depends on jurisdiction and use."),
      "Token design spans software engineering, economics and compliance.", True, "Current jurisdictional law and official guidance."),
    T("coin_vs_token", "Coin vs Token", "digital_assets", ("coin vs token", "coin and token", "difference between coin and token"),
      "A native coin belongs to its own blockchain; a token usually runs on an existing blockchain.",
      ("Native coins participate in their network's fee and security model.", "Tokens inherit much of the host chain's infrastructure.", "Launching a token is generally different from launching a blockchain."),
      "The distinction determines technical architecture and operational responsibilities."),
    T("mining", "Crypto Mining", "digital_assets", ("mining", "bitcoin mining", "mining profitability"),
      "Proof-of-work mining uses computation to compete for block rewards and transaction fees.",
      ("Hash rate measures computations per second.", "Expected reward depends on network share and protocol conditions.", "Electricity, hardware, pool fees and downtime reduce economic return."),
      "Mining profitability is an operating-economics problem, not just a coin-price problem.", True, "Live network and pool data."),
    T("arbitrage", "Crypto Arbitrage", "markets", ("arbitrage", "crypto arbitrage", "cross exchange arbitrage"),
      "Arbitrage attempts to capture price differences for equivalent exposures after transaction and execution costs.",
      ("Compare buy and sell prices.", "Account for fees and slippage.", "Account for transfer, funding, liquidity and timing constraints.", "A displayed spread may disappear before execution."),
      "Observed price differences are not guaranteed realizable profit."),
    T("portfolio", "Portfolio Construction", "portfolio", ("portfolio", "asset allocation", "portfolio construction"),
      "A portfolio combines financial exposures evaluated together.",
      ("Asset allocation determines broad exposure.", "Position size determines concentration.", "Correlation changes portfolio behavior.", "Rebalancing changes weights."),
      "Portfolio analysis considers interaction between positions."),
    T("risk", "Financial Risk", "portfolio", ("risk", "financial risk", "risk and return"),
      "Financial risk is the possibility that realized outcomes differ from expectations, including loss.",
      ("Market risk reflects price changes.", "Credit risk reflects failure to pay.", "Liquidity risk reflects difficulty trading.", "Operational and regulatory risks affect execution."),
      "Risk analysis prevents expected return from being treated as a guarantee."),
    T("cagr", "CAGR", "calculations", ("cagr", "compound annual growth rate"),
      "CAGR is the constant annualized rate connecting a beginning value to an ending value over a period.",
      ("CAGR = (ending / beginning)^(1/years) - 1.", "It does not model interim cash-flow timing.", "IRR or XIRR can be more appropriate with irregular contributions."),
      "CAGR is useful for comparing growth rates."),
    T("capital_gains", "Capital Gains", "taxation", ("capital gains", "capital gain"),
      "A capital gain generally arises when a qualifying asset is transferred for an amount above its relevant cost basis, subject to tax law.",
      ("Identify purchase and sale data.", "Determine holding-period and asset-specific treatment.", "Apply applicable exemptions, rates and adjustments.", "Report under the appropriate return schedule."),
      "Capital-gains computation depends on current law and transaction facts.", True, "Income Tax Department current law and ITR schemas."),
    T("tds", "Tax Deducted at Source", "taxation", ("tds", "tax deducted at source"),
      "TDS is a mechanism in which specified payers deduct tax from specified payments and remit it under the law.",
      ("The payer deducts tax when statutory conditions apply.", "The recipient receives tax credit subject to reporting.", "Certificates and tax statements support reconciliation."),
      "TDS connects payments with tax collection and reporting.", True, "Income Tax Department current TDS rules."),
    T("foreign_investment", "Foreign Investment in India", "foreign_investment", ("foreign investment", "fdi", "fpi", "nri", "oci"),
      "Foreign investment in India is governed by different regimes depending on investor status, instrument, sector and purpose.",
      ("FDI uses sectoral caps and entry routes.", "FPI covers eligible non-resident portfolio investment.", "NRI/OCI routes have specific schedules.", "Reporting and authorised-dealer processes apply."),
      "Classification changes the permitted route and compliance.", True, "RBI foreign-investment direction and current SEBI FPI rules."),
    T("listing_routes", "Listing a Company in India", "capital_markets", ("how to list", "list company", "stock market listing", "listing a company"),
      "A company may use different listing paths depending on issuer type, platform, security and current eligibility.",
      ("Main-board IPO is one route for eligible issuers.", "SME IPO is a specialised route.", "IGP provides a distinct route for eligible issuers.", "Existing listed issuers can use separate fundraising mechanisms.", "Debt securities have their own listing framework."),
      "Separating initial listing from post-listing fundraising avoids mixing different regulatory processes.", True, "SEBI ICDR, LODR and applicable exchange rules."),
    T("rbi_retail_direct", "RBI Retail Direct", "government_securities", ("rbi retail direct", "retail direct"),
      "RBI Retail Direct is a route for eligible retail investors to access specified government securities.",
      ("An eligible investor opens the relevant account.", "Government securities can be selected under platform rules.", "Interest and maturity are handled according to the security's terms."),
      "It connects retail investors with government-securities markets.", True, "RBI Retail Direct official information."),
)


def _normalize(value: str) -> str:
    return " ".join(str(value).strip().lower().split())


def find_topics(query: str, limit: int = 6) -> List[FinanceTopic]:
    normalized = _normalize(query)
    if not normalized:
        return []
    tokens = [t for t in normalized.split() if len(t) >= 3]
    scored: List[tuple[int, FinanceTopic]] = []
    for topic in TOPICS:
        searchable = " ".join((topic.topic_id, topic.title, topic.category, *topic.aliases)).lower()
        exact = max((10 for alias in topic.aliases if _normalize(alias) in normalized), default=0)
        token_score = sum(1 for token in tokens if token in searchable)
        if exact or token_score:
            scored.append((exact + token_score, topic))
    scored.sort(key=lambda pair: (-pair[0], pair[1].topic_id))
    return [topic for _, topic in scored[: max(1, int(limit))]]


def build_answer(query: str, limit: int = 6) -> Dict[str, Any]:
    topics = find_topics(query, limit=limit)
    if not topics:
        return {"found": False, "matches": [], "answer": "", "requires_current_data": False}
    primary = topics[0]
    lines = [primary.title, primary.what_it_is, "", "How it works:"]
    lines.extend("- " + step for step in primary.how_it_works)
    lines.extend(["", "Why it matters: " + primary.why_it_matters])
    if primary.current_data_needed:
        lines.extend(["", "Current-data note: " + (primary.source_hint or "Use a current official/provider source.")])
    if len(topics) > 1:
        lines.extend(["", "Related topics:"])
        lines.extend("- " + topic.title for topic in topics[1:])
    return {
        "found": True,
        "matches": [asdict(topic) for topic in topics],
        "answer": "\n".join(lines),
        "requires_current_data": primary.current_data_needed,
    }
