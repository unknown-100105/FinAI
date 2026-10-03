import { useMemo, useState } from "react";
import { BookOpen, ExternalLink, GraduationCap, Search } from "lucide-react";
import "./PlatformModules.css";

const modules = [
  ["Foundations","Money, money supply, banking, central banks, inflation, interest rates"],
  ["Markets","Stocks, exchanges, order books, price discovery, indices and market microstructure"],
  ["Fixed Income","Bonds, coupons, yields, duration, yield curves, T-bills, repo and money markets"],
  ["Funds","Mutual funds, NAV, SIP, ETFs, REITs, InvITs, PMS and AIFs"],
  ["Derivatives","Futures, options, forwards, swaps, margin, mark-to-market and hedging"],
  ["Portfolio","Asset allocation, diversification, correlation, volatility, drawdown and rebalancing"],
  ["Valuation","P/E, P/B, EV/EBITDA and DCF concepts"],
  ["Personal Finance","Budgeting, emergency funds, loans, EMI, credit scores, insurance and retirement"],
  ["Indian Regulation","SEBI, RBI, FEMA, LODR, ICDR, FPI, FDI and investor protection"],
  ["Tax","ITR, TDS, AIS, 26AS, capital gains, VDA, tax regimes and international tax basics"],
  ["Crypto","Hashing, blockchain, PoW, PoS, wallets, smart contracts, tokens, stablecoins and DeFi"],
  ["Mining","Hash rate, difficulty, block rewards, pools, energy efficiency and unit economics"],
  ["Corporate Finance","Capital structure, cost of capital, dividends, buybacks, IPOs and fundraising"],
  ["Accounting","Balance sheet, P&L, cash flow, working capital, ratios and financial statements"],
];

const links = [
  ["SEBI Investor", "https://investor.sebi.gov.in/"],
  ["RBI Financial Education", "https://www.rbi.org.in/commonperson/English/Scripts/FinancialEducation.aspx"],
  ["Income Tax Help", "https://www.incometax.gov.in/iec/foportal/"],
  ["NISM Investor Education Content", "https://www.nism.ac.in/investor-education-content"],
  ["NISM Investor Education", "https://www.nism.ac.in/investor-education"],
  ["NISM eLearning", "https://online.nism.ac.in/"],
  ["NSE Learn", "https://www.nseindia.com/learn"],
  ["PFRDA NPS", "https://pfrda.org.in/en/schemes/national-pension-system/nps-for-all-citizen-models"],
  ["GST Tutorials", "https://tutorial.gst.gov.in/userguide/returns/"],
];

export function StudyHub() {
  const [query, setQuery] = useState("");
  const filtered = useMemo(
    () => modules.filter(([title, description]) =>
      (title + " " + description).toLowerCase().includes(query.toLowerCase())
    ),
    [query],
  );

  return (
    <section className="module-page">
      <div className="module-hero">
        <div>
          <div className="module-kicker"><GraduationCap size={14} /> Finance study centre</div>
          <h1>One curriculum from money basics to markets, investing, tax and crypto.</h1>
          <p>Study the concepts, then open primary regulator/government sources for India-specific rules and formal learning.</p>
        </div>
        <div className="module-orb"><BookOpen size={23} /></div>
      </div>

      <div className="compliance-search">
        <Search size={14} />
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search finance, tax, crypto, bonds, accounting…" />
      </div>

      <div className="study-grid">
        {filtered.map(([title, description]) => (
          <article className="study-card" key={title}>
            <div className="module-kicker">{title}</div>
            <h3>{title}</h3>
            <p>{description}</p>
            <button type="button" className="secondary-module-button" onClick={() => document.getElementById("study-links")?.scrollIntoView({ behavior: "smooth" })}>
              Open study sources
            </button>
          </article>
        ))}
      </div>

      <section id="study-links" className="workspace-panel">
        <div className="module-panel-head">
          <div><div className="module-kicker"><ExternalLink size={12} /> Official study sources</div><h2>Primary-source learning</h2></div>
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
