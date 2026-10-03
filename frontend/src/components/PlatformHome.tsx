import { ArrowRight, BarChart3, BriefcaseBusiness, FileText, Newspaper, PiggyBank, Sparkles } from "lucide-react";
import "./PlatformModules.css";

type Props = { onNavigate: (section: string) => void };

const modules = [
  ["markets", "Markets", "Stocks, indices, crypto, FX, commodities and technical views.", BarChart3],
  ["investments", "Investments", "Mutual funds, SIPs, bonds, FD, post-office and money market.", PiggyBank],
  ["portfolio", "Portfolio", "Holdings, live valuations, P&L and watchlist.", BriefcaseBusiness],
  ["news", "Financial news", "Market, company and sector headlines with source links.", Newspaper],
  ["forms", "Forms", "Prepare, validate, review and export financial drafts.", FileText],
  ["assistant", "FinAI Assistant", "Natural-language finance with routing and verification.", Sparkles],
] as const;

export function PlatformHome({ onNavigate }: Props) {
  return (
    <section className="platform-page">
      <div className="platform-hero">
        <div>
          <div className="module-kicker"><Sparkles size={14} /> Financial intelligence platform</div>
          <h1>Your financial command center.</h1>
          <p>Markets, investments, portfolio, news, guided forms and an explainable AI assistant in one workspace.</p>
        </div>
        <div className="platform-badge"><Sparkles size={16} /> Evidence-first</div>
      </div>

      <div className="module-grid">
        {modules.map(([id, title, body, Icon]) => (
          <button className="module-card" type="button" key={id} onClick={() => onNavigate(id)}>
            <div className="module-icon"><Icon size={19} /></div>
            <div className="module-copy"><strong>{title}</strong><span>{body}</span></div>
            <ArrowRight size={15} />
          </button>
        ))}
      </div>

      <div className="platform-banner">
        <Sparkles size={17} />
        <div>
          <strong>Ask FinAI, then inspect the structure behind the answer.</strong>
          <span>Routing, authority, retrieval, model selection and verification are exposed in the assistant workspace.</span>
        </div>
      </div>
    </section>
  );
}

export default PlatformHome;
