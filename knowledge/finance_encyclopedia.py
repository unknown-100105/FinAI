"""Finance encyclopedia for deterministic, explainable domain knowledge.

This layer is for broad financial concepts and mechanics. Current market prices,
tax rates, issuer terms and regulatory deadlines must come from current provider
or official-source retrieval rather than this static encyclopedia.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
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


TOPICS = (
    FinanceTopic("money", "Money", "foundations", ("money", "currency", "medium of exchange"),
                 "Money is an accepted medium for exchange, a unit for measuring economic value and a store of purchasing power.",
                 ("Modern monetary systems use money issued within legal and institutional frameworks.", "Bank deposits and physical currency are distinct forms of money.", "The purchasing power of money changes with inflation."),
                 "Money makes exchange, pricing, saving and settlement scalable."),
    FinanceTopic("history_money", "History of Money", "history", ("history of money", "evolution of money", "money history"),
                 "The history of money covers the evolution from commodity forms and coinage to banknotes, commercial bank deposits and modern digital payment systems.",
                 ("Metal coinage made standardized units easier to transfer and verify.", "Banking systems introduced transferable deposits and credit creation.", "Central banks and fiat monetary systems became dominant in modern economies.", "Electronic payments moved settlement increasingly from physical notes to account-based records.", "Cryptographic digital assets created a separate model based on distributed networks."),
                 "Understanding the evolution of money explains why banking, central banks and digital payments work differently."),
    FinanceTopic("bank", "Commercial Banks", "banking", ("bank", "banks", "commercial banking"),
                 "A commercial bank accepts deposits, provides credit and payment services, and manages liquidity, capital and risk.",
                 ("Deposits create bank liabilities while loans are bank assets.", "Banks earn income from lending and services while paying costs on funding.", "Capital and liquidity requirements constrain balance-sheet growth.", "Payment rails allow customers to transfer claims on bank deposits."),
                 "Bank balance sheets connect savings, credit creation, payments and financial stability."),
    FinanceTopic("central_bank", "Central Banking", "monetary_system", ("central bank", "central banking"),
                 "A central bank is a public institution responsible for monetary and financial-system functions defined by its legal mandate.",
                 ("It can influence short-term interest rates and banking-system liquidity.", "It can operate payment and settlement infrastructure or provide oversight depending on the jurisdiction.", "Its policy signals affect borrowing costs, asset prices and currency expectations."),
                 "Central-bank policy is a key transmission mechanism between macroeconomics and financial markets."),
                 True, "RBI for India; central-bank publications for current policy information."),
    FinanceTopic("fiat", "Fiat Money", "monetary_system", ("fiat money", "fiat currency"),
                 "Fiat money is currency that is not redeemable for a fixed amount of a commodity and is supported by legal, monetary and economic institutions.",
                 ("Its value is linked to confidence, monetary policy, economic conditions and acceptance for transactions.", "Supply and demand for money interact with interest rates and economic activity.", "Inflation changes purchasing power over time."),
                 "Fiat systems underpin most modern national currencies."),
    FinanceTopic("history_finance", "History of Finance", "history", ("history of finance", "financial history", "history finance"),
                 "The history of finance traces how societies moved from direct exchange and commodity money toward banking, debt markets, joint-stock companies, modern exchanges, central banking and digital financial networks.",
                 ("Ancient credit and lending practices developed alongside trade.", "Commercial banking and public debt markets expanded as states and merchants needed larger pools of capital.", "Joint-stock companies and organized exchanges widened access to investable securities.", "Central banks and modern payment systems emerged as financial systems became more interconnected.", "Electronic markets and fintech transformed trading and payments, while crypto introduced programmable decentralized networks."),
                 "Historical context helps explain why today's financial institutions, markets and digital assets have different roles."),
    FinanceTopic("inflation", "Inflation", "economics", ("inflation", "price inflation"),
                 "Inflation is a sustained increase in the general level of prices.",
                 ("Price indices summarize changes across baskets of goods and services.", "Higher inflation can reduce the real purchasing power of fixed cash flows.", "Nominal investment returns should be compared with inflation for long-term goals."),
                 "Inflation changes the real value of savings, wages, debt and investments."),
                 True, "Current official CPI and monetary-policy publications."),
    FinanceTopic("monetary_policy", "Monetary Policy", "economics", ("monetary policy", "interest rate policy"),
                 "Monetary policy is the central-bank use of policy instruments and communication to influence monetary and financial conditions.",
                 ("Policy rates influence short-term funding costs.", "Banking-system liquidity affects money-market conditions.", "Changes transmit through loans, deposits, exchange rates, asset prices and demand."),
                 "Monetary policy connects the money market to the wider economy."),
                 True, "RBI monetary-policy statements for India."),
    FinanceTopic("stock", "Stocks / Equities", "markets", ("stock", "stocks", "equity", "equities", "share", "shares"),
                 "A stock represents an ownership interest in a company.",
                 ("A shareholder has an economic claim on the company subject to the security's terms.", "Prices are formed through orders from buyers and sellers.", "Corporate earnings, expectations, rates, liquidity and risk perception can move prices.", "Dividends and capital appreciation are two common return components."),
                 "Equities provide ownership exposure and are traded in primary and secondary markets."),
    FinanceTopic("ipo", "Initial Public Offering", "markets", ("ipo", "initial public offering", "public issue"),
                 "An IPO is a public securities offering associated with a company becoming publicly traded.",
                 ("The offer document describes the business, financials, risks and terms.", "Investors submit bids under the issue mechanism.", "Allocation and subsequent trading follow exchange and regulatory rules."),
                 "IPOs connect private-company financing with public capital markets.", True, "SEBI and exchange issue disclosures."),
    FinanceTopic("bond", "Bonds", "fixed_income", ("bond", "bonds", "fixed income"),
                 "A bond is a debt instrument in which an issuer borrows capital and owes contractual payments to investors.",
                 ("Coupon payments and principal repayment are defined by the issue terms.", "Bond price and yield move inversely under standard fixed-cash-flow assumptions.", "Credit risk, duration and liquidity affect value.", "A bond can trade above or below face value before maturity."),
                 "Bonds finance governments and companies and provide a market-based view of interest rates and credit risk."),
    FinanceTopic("yield", "Bond Yield", "fixed_income", ("bond yield", "yield to maturity", "ytm", "yield"),
                 "Bond yield is a rate used to relate a bond's price to its contractual cash flows under a stated convention.",
                 ("A higher required yield generally implies a lower price for fixed future cash flows.", "Yield to maturity incorporates coupon cash flows and redemption under simplifying assumptions.", "Credit, liquidity and embedded options can make real-market yield interpretation more complex."),
                 "Yield is a core bridge between fixed-income prices, rates and valuation."),
    FinanceTopic("yield_curve", "Yield Curve", "fixed_income", ("yield curve", "term structure", "term structure of interest rates"),
                 "A yield curve shows yields across maturities for a defined set of debt securities or reference rates.",
                 ("Short and long maturities can have different yields.", "The curve reflects expectations, term premia, liquidity and market conditions.", "Changes in curve shape matter for borrowing, valuation and interest-rate risk."),
                 "The yield curve summarizes the time dimension of interest rates.", True, "RBI and government-securities market data."),
    FinanceTopic("money_market", "Money Market", "fixed_income", ("money market", "money markets"),
                 "The money market covers short-term borrowing and lending instruments and liquidity management.",
                 ("India's overnight market includes collateralised and uncollateralised segments.", "Treasury bills and other short-duration instruments can serve liquidity and financing needs.", "Credit and liquidity characteristics vary by instrument."),
                 "Money markets are central to day-to-day funding and monetary-policy transmission.",
                 True, "RBI money-market and government-securities publications."),
    FinanceTopic("repo", "Repo", "money_market", ("repo", "repurchase agreement", "reverse repo"),
                 "A repo is a financing transaction structured around the sale and repurchase of securities.",
                 ("One party receives cash against securities collateral.", "The securities are repurchased under agreed terms.", "Repo rates are important short-term funding prices.", "Central banks can use repo-style operations as monetary-policy tools."),
                 "Repo markets support liquidity and collateralized short-term financing."),
                 True, "RBI market-operations publications."),
    FinanceTopic("treasury_bill", "Treasury Bills", "government_securities", ("treasury bill", "treasury bills", "t-bill", "t bills"),
                 "Treasury bills are short-term government securities issued at a discount or under the applicable auction convention and redeemed at maturity.",
                 ("They have short maturities.", "Auction yields determine issue economics.", "Because their credit exposure is to the sovereign within the applicable framework, they are widely used as short-term reference instruments."),
                 "T-bills form a key component of government financing and money-market benchmarks.", True, "RBI and Government of India auction notifications."),
    FinanceTopic("mutual_fund", "Mutual Funds", "investments", ("mutual fund", "mutual funds", "mf"),
                 "A mutual fund pools investor money and invests it under a stated scheme mandate.",
                 ("Investors receive units representing proportional interests.", "The portfolio is managed according to scheme documents.", "NAV reflects the portfolio's valuation under the scheme's valuation rules.", "Costs, liquidity, risk and tax treatment depend on the scheme and investor."),
                 "Mutual funds package diversified market exposure into an accessible pooled structure.", True, "SEBI scheme documents and current factsheets."),
    FinanceTopic("sip", "Systematic Investment Plan", "investments", ("sip", "systematic investment plan"),
                 "A SIP is a recurring contribution method, commonly used to invest in mutual funds at scheduled intervals.",
                 ("The investor contributes a chosen amount at each interval.", "The amount buys units at the applicable NAV.", "The quantity of units varies with price.", "Returns are market-dependent."),
                 "SIPs automate recurring investing but do not guarantee returns."),
    FinanceTopic("etf", "Exchange-Traded Funds", "investments", ("etf", "etfs", "exchange traded fund"),
                 "An ETF is a pooled investment vehicle whose units trade on an exchange.",
                 ("Market price changes during trading hours.", "The traded price can differ slightly from NAV.", "Bid-ask spread and tracking difference matter.", "Some ETFs track indices, commodities or other permitted assets."),
                 "ETFs combine pooled-fund exposure with exchange trading."),
    FinanceTopic("derivatives", "Derivatives", "markets", ("derivative", "derivatives"),
                 "A derivative is a financial contract whose value depends on an underlying asset, rate, index or event.",
                 ("The contract defines payoff conditions.", "Participants can use derivatives for hedging, exposure or risk transfer.", "Leverage can amplify gains and losses.", "Margining and settlement rules depend on the market."),
                 "Derivatives connect hedging and speculative exposures to underlying markets."),
    FinanceTopic("futures", "Futures", "derivatives", ("future", "futures contract", "futures"),
                 "A futures contract standardizes an agreement to transact or settle against an underlying at a future date or according to the market's cash-settlement convention.",
                 ("Contracts specify the underlying, expiry, contract size and settlement mechanism.", "Positions are usually marked to market and margined.", "The futures price may differ from spot because of carry, funding, dividends and other factors."),
                 "Futures provide standardized leveraged exposure and hedging."),
    FinanceTopic("options", "Options", "derivatives", ("option", "options", "call option", "put option"),
                 "An option gives its holder a right, not an obligation, under the contract terms, while the seller has a corresponding obligation.",
                 ("Calls relate to upside rights and puts to downside rights under standard definitions.", "The buyer pays a premium.", "Value depends on strike, expiry, underlying price, volatility, rates and other inputs.", "Option writers face asymmetric obligations."),
                 "Options reshape risk through nonlinear payoffs."),
    FinanceTopic("market_orderbook", "Order Book and Price Discovery", "markets", ("order book", "market order", "limit order", "price discovery"),
                 "An order book records resting buy and sell orders for a traded instrument.",
                 ("The best bid is the highest displayed buy price.", "The best ask is the lowest displayed sell price.", "The spread is the difference between them.", "Trades occur when compatible orders interact.", "Depth and liquidity affect execution quality."),
                 "Order books explain how quotes become actual trades."),
    FinanceTopic("market_cap", "Market Capitalization", "markets", ("market cap", "market capitalization"),
                 "Market capitalization is commonly calculated as market price multiplied by the number of shares outstanding.",
                 ("It changes with the share price and share count.", "It is different from enterprise value.", "Market cap is a size measure, not a complete valuation model."),
                 "Market capitalization is a common way to describe equity-market size.", True, "Current exchange/company share-count and price data."),
    FinanceTopic("pe", "Price-to-Earnings Ratio", "valuation", ("p/e", "pe ratio", "price to earnings"),
                 "P/E compares market price with earnings per share under a stated earnings basis.",
                 ("It can be trailing or forward.", "Negative earnings can make P/E unusable.", "Sector growth, cyclicality and accounting matter.", "A single P/E should not be interpreted without context."),
                 "P/E is one of several valuation measures."),
    FinanceTopic("banking_payments", "Payments and Settlement", "payments", ("payments", "payment systems", "settlement"),
                 "A payment system transfers value or the financial claims representing value between parties.",
                 ("Messaging, authorization and settlement are separate functions.", "Banks or payment institutions may maintain the underlying accounts.", "Final settlement depends on the payment rail and operating rules."),
                 "Payment systems connect money to real-world commerce."),
    FinanceTopic("upi", "UPI", "payments", ("upi", "unified payments interface"),
                 "UPI is an Indian interoperable payment system enabling account-to-account transactions through participating institutions.",
                 ("A payer initiates a payment request through a supported app.", "The transaction is routed through the participating payment ecosystem.", "Authorization, risk checks and settlement happen according to the scheme and bank processes."),
                 "UPI is an example of interoperable retail payment infrastructure.", True, "NPCI operating documents and participant-bank information."),
    FinanceTopic("rtgs", "RTGS", "payments", ("rtgs", "real time gross settlement"),
                 "RTGS is a payment system in which transactions are settled individually in real time according to system rules.",
                 ("Payment instructions are processed through the RTGS system.", "Settlement is gross rather than netted across a batch.", "It is used for high-value or time-critical transfers under the applicable rules."),
                 "RTGS illustrates central-bank settlement infrastructure.", True, "RBI RTGS information."),
    FinanceTopic("neft", "NEFT", "payments", ("neft", "national electronic funds transfer"),
                 "NEFT is an electronic funds-transfer system operated under RBI rules.",
                 ("Customers initiate transfer instructions through participating institutions.", "Transactions are processed through the NEFT system.", "Timing, limits and charges depend on current operating rules."),
                 "NEFT is a major account-to-account transfer rail in India.", True, "RBI NEFT information."),
    FinanceTopic("crypto", "Cryptocurrency", "digital_assets", ("crypto", "cryptocurrency", "cryptocurrencies"),
                 "Cryptoassets are digitally represented assets that can use cryptographic verification and distributed-ledger technology.",
                 ("Ownership records can be maintained on a blockchain or other distributed system.", "Transactions are authorized using cryptographic keys.", "Markets trade on centralized or decentralized venues.", "Risks include volatility, custody, technology, counterparty and regulatory exposure."),
                 "Crypto combines technology, market structure and asset-price risk.", True, "Current legal, tax and platform rules must be verified."),
    FinanceTopic("bitcoin", "Bitcoin", "digital_assets", ("bitcoin", "btc"),
                 "Bitcoin is a decentralized cryptoasset network with a native unit used for value transfer and settlement within its protocol.",
                 ("Transactions are broadcast to the network.", "Mining and proof-of-work are used to order and secure blocks.", "Supply follows protocol-defined issuance and halving mechanics.", "Users control assets through private keys."),
                 "Bitcoin is a foundational example of a permissionless digital-asset network.", True, "Bitcoin protocol documentation and current market data."),
    FinanceTopic("blockchain", "Blockchain", "digital_assets", ("blockchain", "distributed ledger", "distributed ledger technology", "dlt"),
                 "A blockchain is a distributed ledger structure in which records are grouped into linked blocks under a network's consensus rules.",
                 ("Participants validate proposed state changes.", "Consensus determines which history is accepted.", "Cryptographic links make retrospective modification difficult under the protocol's assumptions.", "Different blockchains use different security and governance designs."),
                 "Blockchain is the infrastructure concept behind many digital assets and DLT applications."),
    FinanceTopic("pow", "Proof of Work", "digital_assets", ("proof of work", "pow"),
                 "Proof of work is a consensus design that makes block production depend on computational work.",
                 ("Miners compete to solve a computational puzzle.", "The accepted chain represents the work recognized by the protocol.", "Attack cost depends on available computation and network economics."),
                 "Proof of work links network security to computation and energy use."),
    FinanceTopic("pos", "Proof of Stake", "digital_assets", ("proof of stake", "pos"),
                 "Proof of stake is a consensus design where block proposal and validation power is linked to staked economic value under protocol rules.",
                 ("Validators lock or delegate stake.", "Protocol rules select or assign validators to participate in consensus.", "Penalties can apply to certain misbehavior.", "Security depends on economics and governance assumptions."),
                 "Proof of stake changes the security model relative to proof of work."),
    FinanceTopic("stablecoin", "Stablecoins", "digital_assets", ("stablecoin", "stablecoins"),
                 "A stablecoin is a cryptoasset designed to maintain a target value, commonly relative to a fiat currency.",
                 ("The stabilization mechanism depends on the design.", "Reserve-backed models depend on assets, custody and redemption arrangements.", "Algorithmic or crypto-collateralized designs use different mechanisms and risks."),
                 "Stablecoins link crypto market infrastructure with money-like settlement use cases.", True, "Current issuer disclosures and regulatory treatment."),
    FinanceTopic("defi", "Decentralized Finance", "digital_assets", ("defi", "decentralized finance"),
                 "DeFi refers to financial applications implemented with smart contracts and decentralized networks.",
                 ("Smart contracts encode transaction and market rules.", "Users interact through wallets rather than conventional account relationships in many designs.", "Lending, exchanges and derivatives can be implemented with on-chain mechanisms.", "Smart-contract, oracle, liquidity and governance risk can be significant."),
                 "DeFi demonstrates how financial market functions can be represented as programmable protocols."),
    FinanceTopic("wallet", "Crypto Wallets and Custody", "digital_assets", ("crypto wallet", "wallet", "self custody", "custody"),
                 "A crypto wallet manages cryptographic keys used to authorize transactions; the blockchain records the assets.",
                 ("A private key or signing mechanism authorizes transfers.", "Self-custody leaves key management with the user.", "Custodial platforms hold keys on behalf of customers.", "Loss or compromise of keys can permanently affect access."),
                 "Custody is one of the most important operational risks in digital assets."),
    FinanceTopic("arbitrage", "Arbitrage", "markets", ("arbitrage", "cross exchange arbitrage"),
                 "Arbitrage is the attempt to capture a price discrepancy for economically equivalent exposures after costs.",
                 ("A trader identifies a buy price and sell price.", "Fees, slippage, funding, transfer costs and taxes reduce the spread.", "Execution timing and liquidity determine whether the observed spread is actually tradable."),
                 "A displayed price difference is not the same as realizable profit."),
    FinanceTopic("portfolio", "Portfolio Construction", "portfolio", ("portfolio", "asset allocation", "portfolio construction"),
                 "A portfolio is a collection of financial exposures evaluated together for risk, return, liquidity and diversification.",
                 ("Asset allocation distributes capital across asset classes.", "Position sizes determine concentration.", "Correlation affects portfolio behavior.", "Rebalancing changes exposures over time."),
                 "Portfolio-level analysis is more informative than looking at one asset in isolation."),
    FinanceTopic("risk_return", "Risk and Return", "portfolio", ("risk return", "risk and return"),
                 "Investment risk is the possibility that realized outcomes differ from expected outcomes, including loss.",
                 ("Different risks include market, credit, liquidity, operational and regulatory risk.", "Higher expected return often comes with greater uncertainty rather than a guarantee of higher realized return.", "Diversification can reduce some concentration risk."),
                 "Understanding risk prevents return targets from being interpreted as guarantees."),
    FinanceTopic("cagr", "CAGR", "calculations", ("cagr", "compound annual growth rate"),
                 "CAGR expresses the constant annualized growth rate that connects a starting value to an ending value over a period.",
                 ("CAGR = (Ending value / Beginning value)^(1/years) - 1.", "It ignores interim cash-flow timing.", "XIRR/IRR can be more appropriate when there are irregular contributions or withdrawals."),
                 "CAGR is useful for comparing growth rates across periods."),
    FinanceTopic("capital_gains", "Capital Gains", "taxation", ("capital gains", "capital gain", "investment tax", "tax on investments"),
                 "A capital gain generally arises when an asset is transferred for more than its relevant cost basis, subject to the governing tax rules.",
                 ("The tax treatment depends on asset type, holding period, transaction date and applicable law.", "Records should include purchase cost, sale proceeds and eligible transaction costs.", "Different assets can be taxed differently."),
                 "Capital-gains analysis requires current tax law and transaction-level records.", True, "Income Tax Department current law, notifications and ITR schemas."),
    FinanceTopic("tds", "Tax Deducted at Source", "taxation", ("tds", "tax deducted at source"),
                 "TDS is a mechanism under which tax is deducted by a specified payer before making certain payments and remitted under the applicable rules.",
                 ("The payer deducts tax when the statutory conditions are met.", "The recipient receives a TDS credit subject to reporting and reconciliation.", "Certificates and tax statements help reconcile the credit."),
                 "TDS connects income payments with advance collection and tax reporting.", True, "Income Tax Department and current TDS rules."),
)


def _normalize(value: str) -> str:
    return " ".join(str(value).strip().lower().split())


def find_topics(query: str, limit: int = 4) -> List[FinanceTopic]:
    normalized = _normalize(query)
    if not normalized:
        return []

    scored: List[tuple[int, FinanceTopic]] = []
    for topic in TOPICS:
        score = 0
        for alias in topic.aliases:
            alias_n = _normalize(alias)
            if alias_n in normalized:
                score += 8 if " " in alias_n else 5
        if topic.category.replace("_", " ") in normalized:
            score += 1
        if score:
            scored.append((score, topic))

    scored.sort(key=lambda item: (-item[0], item[1].topic_id))
    return [topic for _, topic in scored[: max(1, int(limit))]]


def build_answer(query: str, limit: int = 4) -> Dict[str, Any]:
    topics = find_topics(query, limit=limit)
    if not topics:
        return {"found": False, "matches": [], "answer": "", "requires_current_data": False}

    primary = topics[0]
    lines = [primary.title, primary.what_it_is, "", "How it works:"]
    lines.extend(f"- {step}" for step in primary.how_it_works)
    lines.extend(["", f"Why it matters: {primary.why_it_matters}"])

    if primary.current_data_needed:
        lines.extend([
            "",
            f"Current-data note: {primary.source_hint or 'Use a current official/provider source for live facts.'}",
        ])

    if len(topics) > 1:
        lines.extend(["", "Related topics:"])
        lines.extend(f"- {topic.title}: {topic.what_it_is}" for topic in topics[1:])

    return {
        "found": True,
        "matches": [asdict(topic) for topic in topics],
        "answer": "\n".join(lines),
        "requires_current_data": primary.current_data_needed,
    }
