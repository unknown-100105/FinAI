import { useMemo, useState } from "react";
import { ArrowRight, BookOpen, ExternalLink, GraduationCap, Search } from "lucide-react";
import "./PlatformModules.css";

type StudyModule = {
  title: string;
  description: string;
  why: string;
  learn: string[];
  source: string;
  url: string;
};

const modules: StudyModule[] = [
  { title: "Foundations", description: "Money, money supply, banking, central banks, inflation and interest rates.", why: "These concepts explain how the financial system creates, prices and moves money.", learn: ["Money and money supply", "Inflation and interest", "Banking and central banks"], source: "RBI Financial Education", url: "https://www.rbi.org.in/commonperson/English/Scripts/FinancialEducation.aspx" },
  { title: "Markets", description: "Stocks, exchanges, order books, price discovery, indices and market microstructure.", why: "Understand how a quoted price becomes an actual market price.", learn: ["Order books", "Price discovery", "Indices and exchanges"], source: "NSE Learn", url: "https://www.nseindia.com/learn" },
  { title: "Fixed Income", description: "Bonds, coupons, yields, duration, yield curves, T-bills, repo and money markets.", why: "Fixed income helps you understand interest-rate risk and defensive portfolios.", learn: ["Bond pricing", "Yield and duration", "Government securities"], source: "RBI", url: "https://www.rbi.org.in/" },
  { title: "Funds", description: "Mutual funds, NAV, SIP, ETFs, REITs, InvITs, PMS and AIFs.", why: "Funds let investors access diversified portfolios through pooled structures.", learn: ["NAV and units", "SIP mechanics", "ETF and fund structures"], source: "SEBI Investor", url: "https://investor.sebi.gov.in/" },
  { title: "Derivatives", description: "Futures, options, forwards, swaps, margin, mark-to-market and hedging.", why: "Derivatives are used for risk transfer, hedging and exposure management.", learn: ["Futures and options", "Margin and MTM", "Hedging concepts"], source: "NSE Learn", url: "https://www.nseindia.com/learn" },
  { title: "Portfolio", description: "Asset allocation, diversification, correlation, volatility, drawdown and rebalancing.", why: "Portfolio construction is about balancing return objectives with risk and concentration.", learn: ["Diversification", "Correlation", "Rebalancing"], source: "SEBI Investor", url: "https://investor.sebi.gov.in/" },
  { title: "Valuation", description: "P/E, P/B, EV/EBITDA and DCF concepts.", why: "Valuation connects a company's financial fundamentals to an estimated economic value.", learn: ["Relative valuation", "Enterprise value", "DCF logic"], source: "NSE Learn", url: "https://www.nseindia.com/learn" },
  { title: "Personal Finance", description: "Budgeting, emergency funds, loans, EMI, credit scores, insurance and retirement.", why: "Personal finance turns financial concepts into everyday decisions.", learn: ["Budget and cash flow", "Loans and EMI", "Retirement planning"], source: "RBI Financial Education", url: "https://www.rbi.org.in/commonperson/English/Scripts/FinancialEducation.aspx" },
  { title: "Indian Regulation", description: "SEBI, RBI, FEMA, LODR, ICDR, FPI, FDI and investor protection.", why: "Regulatory rules determine what an investor or company can legally do.", learn: ["SEBI framework", "RBI/FEMA concepts", "Investor protection"], source: "SEBI Investor", url: "https://investor.sebi.gov.in/" },
  { title: "Tax", description: "ITR, TDS, AIS, 26AS, capital gains, VDA, tax regimes and international tax basics.", why: "Tax treatment can materially change the economic outcome of a financial decision.", learn: ["Return filing", "TDS/AIS reconciliation", "Capital-gains concepts"], source: "Income Tax Department", url: "https://www.incometax.gov.in/iec/foportal/" },
  { title: "Crypto", description: "Hashing, blockchain, PoW, PoS, wallets, smart contracts, tokens, stablecoins and DeFi.", why: "Understand the technology and risk structure before evaluating digital-asset products.", learn: ["Consensus", "Wallets and keys", "Smart contracts"], source: "NSE Learn", url: "https://www.nseindia.com/learn" },
  { title: "Mining", description: "Hash rate, difficulty, block rewards, pools, energy efficiency and unit economics.", why: "Mining economics depend on network conditions, hardware efficiency and operating costs.", learn: ["Hash rate", "Difficulty", "Unit economics"], source: "NSE Learn", url: "https://www.nseindia.com/learn" },
  { title: "Corporate Finance", description: "Capital structure, cost of capital, dividends, buybacks, IPOs and fundraising.", why: "Corporate finance explains how companies fund growth and return capital.", learn: ["Cost of capital", "Capital structure", "Fundraising"], source: "NSE Learn", url: "https://www.nseindia.com/learn" },
  { title: "Accounting", description: "Balance sheet, P&L, cash flow, working capital, ratios and financial statements.", why: "Accounting statements are the evidence layer behind many investment and credit decisions.", learn: ["Three statements", "Working capital", "Financial ratios"], source: "NISM Investor Education", url: "https://www.nism.ac.in/investor-education-content" },
];

const links = [
  ["SEBI Investor", "https://investor.sebi.gov.in/"],
  ["RBI Financial Education", "https://www.rbi.org.in/commonperson/English/Scripts/FinancialEducation.aspx"],
  ["Income Tax Help", "https://www.incometax.gov.in/iec/foportal/"],
  ["NISM Investor Education Content", "https://www.nism.ac.in/investor-education-content"],
  ["NSE Learn", "https://www.nseindia.com/learn"],
  ["PFRDA NPS", "https://pfrda.org.in/en/schemes/national-pension-system/nps-for-all-citizen-models"],
  ["GST Tutorials", "https://tutorial.gst.gov.in/userguide/returns/"],
];

export function StudyHub() {
  const [query, setQuery] = useState("");
  const [selectedTitle, setSelectedTitle] = useState("Foundations");
  const filtered = useMemo(
    () => modules.filter((item) => (item.title + " " + item.description + " " + item.why + " " + item.learn.join(" ")).toLowerCase().includes(query.toLowerCase())),
    [query],
  );
  const selected = modules.find((item) => item.title === selectedTitle) ?? filtered[0] ?? modules[0];

  return (
    <section className="module-page study-centre-page">
      <div className="module-hero">
        <div>
          <div className="module-kicker"><GraduationCap size={14} /> Finance study centre</div>
          <h1>Learn the concept before you open the rulebook.</h1>
          <p>Each module explains what you are learning, why it matters, the core topics and a directly linked primary learning source.</p>
        </div>
        <div className="module-orb"><BookOpen size={23} /></div>
      </div>

      <div className="compliance-search">
        <Search size={14} />
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search finance, tax, crypto, bonds, accounting…" />
      </div>

      <div className="study-workspace">
        <section className="study-module-grid">
          {filtered.map((item) => (
            <button type="button" className={selected?.title === item.title ? "study-card active" : "study-card"} key={item.title} onClick={() => setSelectedTitle(item.title)}>
              <div className="module-kicker">{item.title}</div>
              <h3>{item.title}</h3>
              <p>{item.description}</p>
              <span><ArrowRight size={12} /> Learn this module</span>
            </button>
          ))}
        </section>

        <aside className="workspace-panel study-brief">
          <div className="module-panel-head">
            <div><div className="module-kicker"><GraduationCap size={12} /> Lesson brief</div><h2>{selected.title}</h2></div>
            <span className="source-chip">Selected</span>
          </div>
          <div className="study-brief-block">
            <span>What is it?</span>
            <p>{selected.description}</p>
          </div>
          <div className="study-brief-block">
            <span>Why should I learn/use it?</span>
            <p>{selected.why}</p>
          </div>
          <div className="study-brief-block">
            <span>Core topics</span>
            <div className="criteria-list">{selected.learn.map((item) => <span key={item}>• {item}</span>)}</div>
          </div>
          <a className="primary-module-button link-button" href={selected.url} target="_blank" rel="noreferrer">
            <ExternalLink size={13} /> Open {selected.source}
          </a>
        </aside>
      </div>

      <section className="workspace-panel">
        <div className="module-panel-head">
          <div><div className="module-kicker"><ExternalLink size={12} /> Official study library</div><h2>Primary-source learning</h2></div>
          <span className="source-chip">External official sources</span>
        </div>
        {links.map(([name, url]) => (
          <a className="news-item" key={name} href={url} target="_blank" rel="noreferrer">
            <div><strong>{name}</strong><span>{url}</span></div>
            <ExternalLink size={12} />
          </a>
        ))}
      </section>
    </section>
  );
}

export default StudyHub;
