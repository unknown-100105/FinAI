import { BookOpen, ChartCandlestick, ClipboardList, Coins, FileCheck2, GraduationCap, Landmark, Sparkles, Wallet } from "lucide-react";
import "./PlatformModules.css";

type Props = { onNavigate:(section:string)=>void };

const items = [
  ["markets","Markets",ChartCandlestick,"Live quotes, OHLCV candles, intervals and technical analytics."],
  ["analyst","Market Analyst",Sparkles,"Inspect each candle, contextual news, scenarios and model backtests."],
  ["investments","Investments",Coins,"Compare funds, deposits, bonds and small-savings calculators."],
  ["resources","Schemes & Resources",Landmark,"Official scheme links, source dates and universal form drafts."],
  ["forms","Tax & Forms",FileCheck2,"ITR, TDS, GST, tax worksheets and filing workflow references."],
  ["arbitrage","Crypto Arbitrage",Wallet,"Pair universe, live spreads, cross-venue analysis and mining economics."],
  ["study","Study Centre",GraduationCap,"Finance, investing, markets, accounting, tax and crypto learning paths."],
  ["knowledge","Knowledge",BookOpen,"SEBI, RBI, FEMA, FDI/FPI, listing and crypto-regulation explainers."],
] as const;

export function PlatformGuide({onNavigate}:Props){
 return <div className="platform-guide">
   <div className="guide-heading"><Sparkles size={14}/><div><strong>FinAI guide</strong><span>Tell me what you are trying to do and I will point you to the right workspace.</span></div></div>
   <div className="guide-grid">
    {items.map(([id,title,Icon,body])=><button type="button" className="guide-card" key={id} onClick={()=>onNavigate(id)}><Icon size={15}/><div><strong>{title}</strong><span>{body}</span></div></button>)}
   </div>
   <div className="guide-tip">Examples: “Explain this candle”, “Where can an NRI invest?”, “Show today's TCS movement”, “How do I list a company?”, or “Open ITR-2 form workflow.”</div>
 </div>
}
export default PlatformGuide;
