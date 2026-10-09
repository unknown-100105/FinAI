import { useMemo, useState } from "react";
import {
  BarChart3,
  Calculator,
  ExternalLink,
  FileSearch,
  Gauge,
  LineChart,
  ShieldCheck,
  Sparkles,
  Table2,
  TrendingDown,
} from "lucide-react";

const money = (value: unknown) =>
  Number.isFinite(Number(value))
    ? new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 0,
      }).format(Number(value))
    : "—";

const number = (value: unknown) =>
  Number.isFinite(Number(value))
    ? Number(value).toLocaleString("en-IN", { maximumFractionDigits: 2 })
    : "—";

function emiSchedule(principal: number, annualRate: number, baseEmi: number, months: number) {
  const monthlyRate = annualRate / 100 / 12;
  let balance = principal;
  const rows: Array<{
    month: number;
    payment: number;
    interest: number;
    principal: number;
    balance: number;
  }> = [];

  for (let month = 1; month <= months && balance > 0.005; month += 1) {
    const interest = monthlyRate === 0 ? 0 : balance * monthlyRate;
    const principalPart = Math.min(balance, Math.max(0, baseEmi - interest));
    const payment = interest + principalPart;
    balance = Math.max(0, balance - principalPart);
    rows.push({
      month,
      payment,
      interest,
      principal: principalPart,
      balance,
    });

    if (payment <= 0) break;
  }

  return rows;
}

function amortizeWithExtra(
  principal: number,
  annualRate: number,
  baseEmi: number,
  extraMonthly: number,
  annualPrepayment: number,
) {
  const monthlyRate = annualRate / 100 / 12;
  let balance = principal;
  let totalInterest = 0;
  let totalPayment = 0;
  let month = 0;

  while (balance > 0.005 && month < 1200) {
    month += 1;
    const interest = monthlyRate === 0 ? 0 : balance * monthlyRate;
    let principalPart = Math.max(0, baseEmi + extraMonthly - interest);
    principalPart = Math.min(principalPart, balance);
    balance -= principalPart;
    totalInterest += interest;
    totalPayment += interest + principalPart;

    if (annualPrepayment > 0 && month % 12 === 0 && balance > 0) {
      const prepayment = Math.min(annualPrepayment, balance);
      balance -= prepayment;
      totalPayment += prepayment;
    }

    if (baseEmi + extraMonthly <= interest && annualPrepayment === 0) break;
  }

  return {
    months: month,
    totalInterest,
    totalPayment,
  };
}

function Stat({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="chat-result-stat">
      <span>{label}</span>
      <strong>{value}</strong>
      {sub && <small>{sub}</small>}
    </div>
  );
}

function XAIButton({ traceId, onNavigate }: { traceId?: string; onNavigate?: (section: any) => void }) {
  if (!traceId || !onNavigate) return null;

  const open = () => {
    localStorage.setItem("finai.currentTraceId", traceId);
    onNavigate("xai");
  };

  return (
    <button type="button" className="chat-result-xai" onClick={open}>
      <FileSearch size={12} /> Inspect XAI trace
    </button>
  );
}

function EMIResultCard({ finance, traceId, onNavigate }: { finance: any; traceId?: string; onNavigate?: (section: any) => void }) {
  const result = finance?.result;
  const [extraMonthly, setExtraMonthly] = useState(5000);
  const [annualPrepayment, setAnnualPrepayment] = useState(50000);
  const [showSchedule, setShowSchedule] = useState(false);

  // Hooks must run in the same order even when the API result is absent.
  // Safe numeric fallbacks let memoized calculations run before the null guard.
  const principal = Number(result?.principal ?? 0);
  const annualRate = Number(result?.annual_rate ?? 0);
  const baseEmi = Number(result?.monthly_emi ?? 0);
  const months = Number(result?.tenure_months ?? 0);
  const schedule = useMemo(
    () => emiSchedule(principal, annualRate, baseEmi, months),
    [principal, annualRate, baseEmi, months],
  );

  const baseline = {
    months: schedule.length,
    totalInterest: Number(result.total_interest),
    totalPayment: Number(result.total_payment),
  };

  const withExtra = useMemo(
    () => amortizeWithExtra(principal, annualRate, baseEmi, extraMonthly, 0),
    [principal, annualRate, baseEmi, extraMonthly],
  );

  const withAnnual = useMemo(
    () => amortizeWithExtra(principal, annualRate, baseEmi, 0, annualPrepayment),
    [principal, annualRate, baseEmi, annualPrepayment],
  );

  const both = useMemo(
    () => amortizeWithExtra(principal, annualRate, baseEmi, extraMonthly, annualPrepayment),
    [principal, annualRate, baseEmi, extraMonthly, annualPrepayment],
  );

  if (!result) return null;

  return (
    <section className="chat-result-card emi-result-card">
      <div className="chat-result-head">
        <div>
          <div className="chat-result-kicker"><Calculator size={12} /> Deterministic finance engine</div>
          <h3>EMI calculation & interest optimizer</h3>
        </div>
        <span className="chat-result-source">Authority: finance engine</span>
      </div>

      <div className="chat-result-stats">
        <Stat label="Principal" value={money(principal)} />
        <Stat label="Interest rate" value={`${annualRate}%`} />
        <Stat label="Monthly EMI" value={money(baseEmi)} />
        <Stat label="Total interest" value={money(result.total_interest)} />
        <Stat label="Total payable" value={money(result.total_payment)} />
        <Stat label="Tenure" value={`${months} months`} sub={`${(months / 12).toFixed(1)} years`} />
      </div>

      <div className="chat-result-section-title"><Table2 size={12} /> Month-by-month amortization</div>
      <div className="emi-schedule-wrap">
        <table className="emi-schedule">
          <thead><tr><th>Month</th><th>Payment</th><th>Interest</th><th>Principal</th><th>Balance</th></tr></thead>
          <tbody>
            {(showSchedule ? schedule : schedule.slice(0, 12)).map((row) => (
              <tr key={row.month}>
                <td>{row.month}</td>
                <td>{money(row.payment)}</td>
                <td>{money(row.interest)}</td>
                <td>{money(row.principal)}</td>
                <td>{money(row.balance)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {schedule.length > 12 && (
        <button type="button" className="chat-result-expand" onClick={() => setShowSchedule((value) => !value)}>
          <Table2 size={11} /> {showSchedule ? "Show first 12 months" : `Show all ${schedule.length} months`}
        </button>
      )}

      <div className="chat-result-section-title"><TrendingDown size={12} /> How to reduce total interest</div>
      <div className="emi-optimizer">
        <label>
          <span>Extra payment every month <b>{money(extraMonthly)}</b></span>
          <input type="range" min="0" max="30000" step="500" value={extraMonthly} onChange={(event) => setExtraMonthly(Number(event.target.value))} />
        </label>
        <label>
          <span>Extra yearly prepayment <b>{money(annualPrepayment)}</b></span>
          <input type="range" min="0" max="300000" step="5000" value={annualPrepayment} onChange={(event) => setAnnualPrepayment(Number(event.target.value))} />
        </label>
      </div>

      <div className="emi-scenarios">
        <div><span>Current schedule</span><strong>{money(baseline.totalInterest)}</strong><small>{baseline.months} months</small></div>
        <div><span>+ monthly extra</span><strong>{money(withExtra.totalInterest)}</strong><small>save {money(Math.max(0, baseline.totalInterest - withExtra.totalInterest))}</small></div>
        <div><span>+ annual prepayment</span><strong>{money(withAnnual.totalInterest)}</strong><small>save {money(Math.max(0, baseline.totalInterest - withAnnual.totalInterest))}</small></div>
        <div className="recommended"><span>Use both</span><strong>{money(both.totalInterest)}</strong><small>save {money(Math.max(0, baseline.totalInterest - both.totalInterest))} · finish in {both.months} months</small></div>
      </div>

      <div className="emi-tips">
        <div><Gauge size={12} /><span>Paying extra earlier usually reduces future interest because the outstanding principal falls sooner.</span></div>
        <div><ShieldCheck size={12} /><span>Check your lender's prepayment/foreclosure terms before making a large extra payment.</span></div>
      </div>

      <div className="chat-result-footer">
        <span>Calculated from the authoritative EMI result returned by FinAI.</span>
        <XAIButton traceId={traceId} onNavigate={onNavigate} />
      </div>
    </section>
  );
}

function MarketResultCard({ market, traceId, onNavigate }: { market: any; traceId?: string; onNavigate?: (section: any) => void }) {
  const results = Array.isArray(market?.results) ? market.results : [];
  const quote = results.find((item: any) => item.operation === "MARKET_QUOTE")?.result;
  const history = results.find((item: any) => item.operation === "MARKET_HISTORY");
  const analytics = results.find((item: any) => item.operation === "MARKET_ANALYTICS")?.result;

  if (!quote && !history && !analytics) return null;

  return (
    <section className="chat-result-card market-result-card">
      <div className="chat-result-head">
        <div>
          <div className="chat-result-kicker"><BarChart3 size={12} /> Live / provider market data</div>
          <h3>{quote?.symbol ?? history?.instrument?.display_name ?? "Market result"}</h3>
        </div>
        <span className="chat-result-source">{quote?.source ?? "provider"}</span>
      </div>

      {quote && (
        <>
          <div className="chat-result-stats">
            <Stat label="Latest price" value={quote.observed_price != null ? number(quote.observed_price) : "—"} sub={quote.currency ?? ""} />
            <Stat label="Session close" value={number(quote.latest_session_close)} />
            <Stat label="Open" value={number(quote.open)} />
            <Stat label="High" value={number(quote.high)} />
            <Stat label="Low" value={number(quote.low)} />
            <Stat label="Volume" value={number(quote.volume)} />
          </div>
          <div className="chat-market-meta">
            <span>Observed {quote.timestamp ? new Date(quote.timestamp).toLocaleString() : "latest provider record"}</span>
            <span>Data status: <b>{quote.data_status ?? "available"}</b></span>
          </div>
        </>
      )}

      {analytics && (
        <div className="chat-result-stats market-analytics-stats">
          <Stat label="Cumulative return" value={`${number(analytics.cumulative_return)}%`} />
          <Stat label="Annualized volatility" value={`${number(analytics.annualized_volatility)}%`} />
          <Stat label="Max drawdown" value={`${number(analytics.maximum_drawdown)}%`} />
          <Stat label="SMA 20" value={number(analytics.sma_20)} />
          <Stat label="SMA 50" value={number(analytics.sma_50)} />
          <Stat label="RSI 14" value={number(analytics.rsi_14)} />
        </div>
      )}

      {history?.result && Array.isArray(history.result) && (
        <div className="chat-mini-history">
          <div className="chat-result-section-title"><LineChart size={12} /> Recent OHLC records</div>
          <div className="chat-history-table">
            {history.result.slice(-6).map((bar: any) => (
              <div key={String(bar.timestamp)}><span>{new Date(bar.timestamp).toLocaleDateString()}</span><b>O {number(bar.open)}</b><b>H {number(bar.high)}</b><b>L {number(bar.low)}</b><b>C {number(bar.close)}</b></div>
            ))}
          </div>
        </div>
      )}

      <div className="chat-result-footer">
        <span>Market values are provider-sourced; the LLM does not invent them.</span>
        <button type="button" className="chat-result-link" onClick={() => onNavigate?.("markets")}><ExternalLink size={11} /> Open Markets workspace</button>
        <XAIButton traceId={traceId} onNavigate={onNavigate} />
      </div>
    </section>
  );
}

function KnowledgeResultCard({ knowledge, traceId, onNavigate }: { knowledge: any; traceId?: string; onNavigate?: (section: any) => void }) {
  if (!knowledge) return null;
  return (
    <section className="chat-result-card knowledge-result-card">
      <div className="chat-result-head">
        <div>
          <div className="chat-result-kicker"><Sparkles size={12} /> Evidence-backed knowledge</div>
          <h3>{knowledge.matches?.[0]?.title ?? "Financial explanation"}</h3>
        </div>
        <span className="chat-result-source">{knowledge.source ?? "structured knowledge"}</span>
      </div>
      {Array.isArray(knowledge.matches) && knowledge.matches.length > 0 && (
        <div className="knowledge-tags">{knowledge.matches.slice(0, 4).map((match: any) => <span key={String(match.topic_id ?? match.title)}>{match.title}</span>)}</div>
      )}
      <p className="knowledge-result-copy">{knowledge.answer}</p>
      <div className="chat-result-footer">
        <span>{knowledge.requires_current_data ? "Current-data verification required." : "Static financial concept."}</span>
        <XAIButton traceId={traceId} onNavigate={onNavigate} />
      </div>
    </section>
  );
}

export function AssistantResultCard({ result, traceId, onNavigate }: { result: any; traceId?: string; onNavigate?: (section: any) => void }) {
  if (result?.finance?.operation === "EMI_CALCULATION") {
    return <EMIResultCard finance={result.finance} traceId={traceId} onNavigate={onNavigate} />;
  }
  if (result?.market_data) {
    return <MarketResultCard market={result.market_data} traceId={traceId} onNavigate={onNavigate} />;
  }
  if (result?.knowledge) {
    return <KnowledgeResultCard knowledge={result.knowledge} traceId={traceId} onNavigate={onNavigate} />;
  }
  return null;
}
