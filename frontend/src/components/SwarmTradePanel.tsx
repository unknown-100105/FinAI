import { useEffect, useRef, useState, type FormEvent } from "react";
import { BrainCircuit, LoaderCircle, ShieldAlert, ShieldCheck } from "lucide-react";
import type { MarketBar } from "../api/market";
import { createSwarmTradePlan, type SwarmTradePlan } from "../api/swarmtrade";

type Props = { symbol: string; currentPrice: number | null; bars: MarketBar[]; isLoading: boolean };

const fieldDefaults = {
  entry: "", stop: "", target: "", capital: "100000", riskPct: "0.5",
  agents: "500", maxDailyLoss: "2", dailyLoss: "0", openRisk: "0",
  leverage: "1", marginRate: "1", multiplier: "1", unitStep: "1",
  feeBps: "5", slippageBps: "5", maxLossPerUnit: "", tickSize: "", tickValue: "",
  pipSize: "", pipValue: "", marginPerUnit: "",
};

function numberValue(value: string): number {
  return Number(value);
}


function average(values: number[]): number {
  return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : 0;
}

function clampSignal(value: number): number {
  return Math.max(-1, Math.min(1, Number.isFinite(value) ? value : 0));
}

/** Simple, transparent candle-derived features; these are not trained model outputs. */
function deriveDirectionalSignals(bars: MarketBar[]): Partial<Record<"trend" | "momentum" | "mean_reversion" | "breakout", string>> | null {
  const valid = bars.filter((bar) => Number.isFinite(bar.close) && bar.close > 0
    && Number.isFinite(bar.high) && Number.isFinite(bar.low));
  const closes = valid.map((bar) => bar.close);
  if (closes.length < 6) return null;

  const last = closes[closes.length - 1];
  const sma20 = average(closes.slice(-Math.min(20, closes.length)));
  const sma50 = average(closes.slice(-Math.min(50, closes.length)));
  const trendBase = closes.length >= 50 ? (sma20 - sma50) / sma50 : (last - sma20) / sma20;
  const momentumBase = last / closes[closes.length - 6] - 1;
  const meanReversionBase = (sma20 - last) / sma20;

  const prior = valid.slice(-21, -1);
  const breakoutBars = prior.length ? prior : valid.slice(0, -1);
  const priorHigh = breakoutBars.length ? Math.max(...breakoutBars.map((bar) => bar.high)) : last;
  const priorLow = breakoutBars.length ? Math.min(...breakoutBars.map((bar) => bar.low)) : last;
  const midpoint = (priorHigh + priorLow) / 2;
  const span = Math.max(priorHigh - priorLow, last * 0.0001);
  let breakout = clampSignal(((last - midpoint) / span) * 0.8);
  if (last > priorHigh) breakout = 1;
  else if (last < priorLow) breakout = -1;

  return {
    trend: String(Number(clampSignal(trendBase / 0.03).toFixed(2))),
    momentum: String(Number(clampSignal(momentumBase / 0.05).toFixed(2))),
    mean_reversion: String(Number(clampSignal(meanReversionBase / 0.03).toFixed(2))),
    breakout: String(Number(breakout.toFixed(2))),
  };
}

function fmt(value: number | undefined): string {
  return typeof value === "number" && Number.isFinite(value)
    ? new Intl.NumberFormat("en-IN", { maximumFractionDigits: 4 }).format(value)
    : "—";
}

export function SwarmTradePanel({ symbol, currentPrice, bars, isLoading }: Props) {
  const [selectedSymbol, setSelectedSymbol] = useState(symbol);
  const [assetClass, setAssetClass] = useState<"equity" | "option" | "future" | "crypto" | "forex">("equity");
  const [side, setSide] = useState<"auto" | "long" | "short">("auto");
  const [fields, setFields] = useState({ ...fieldDefaults, entry: currentPrice == null ? "" : String(currentPrice) });
  const [signals, setSignals] = useState({ trend: "0", momentum: "0", mean_reversion: "0", breakout: "0", sentiment: "0" });
  const [result, setResult] = useState<SwarmTradePlan | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const lastSymbol = useRef(symbol);

  useEffect(() => {
    const symbolChanged = lastSymbol.current !== symbol;
    lastSymbol.current = symbol;
    setSelectedSymbol(symbol);
    setFields((previous) => {
      if (symbolChanged) return { ...previous, entry: "" };
      if (previous.entry.trim() || currentPrice == null) return previous;
      return { ...previous, entry: String(currentPrice) };
    });
  }, [symbol, currentPrice]);

  useEffect(() => {
    const derived = deriveDirectionalSignals(bars);
    if (derived) {
      setSignals((previous) => ({ ...previous, ...derived }));
    }
  }, [bars]);

  const update = (key: keyof typeof fieldDefaults, value: string) => {
    setFields((previous) => ({ ...previous, [key]: value }));
  };

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setResult(null);
    try {
      const request = {
        symbol: selectedSymbol.trim(),
        asset_class: assetClass,
        side,
        entry_price: numberValue(fields.entry),
        stop_price: numberValue(fields.stop),
        target_price: numberValue(fields.target),
        capital: numberValue(fields.capital),
        risk_pct: numberValue(fields.riskPct),
        open_position_risk_pct: numberValue(fields.openRisk),
        current_daily_loss_pct: numberValue(fields.dailyLoss),
        max_daily_loss_pct: numberValue(fields.maxDailyLoss),
        max_leverage: numberValue(fields.leverage),
        margin_rate: numberValue(fields.marginRate),
        multiplier: numberValue(fields.multiplier),
        unit_step: numberValue(fields.unitStep),
        fee_bps: numberValue(fields.feeBps),
        slippage_bps: numberValue(fields.slippageBps),
        min_reward_risk: 1,
        agent_count: numberValue(fields.agents),
        ...(assetClass === "option" && fields.maxLossPerUnit.trim()
          ? { max_loss_per_unit: numberValue(fields.maxLossPerUnit) }
          : {}),
        ...(assetClass === "future" ? {
          tick_size: numberValue(fields.tickSize),
          tick_value: numberValue(fields.tickValue),
          margin_per_unit: numberValue(fields.marginPerUnit),
        } : {}),
        ...(assetClass === "forex" ? {
          pip_size: numberValue(fields.pipSize),
          pip_value_per_unit: numberValue(fields.pipValue),
          margin_per_unit: numberValue(fields.marginPerUnit),
        } : {}),
        signals: Object.fromEntries(
          Object.entries(signals).map(([key, value]) => [key, numberValue(value)]),
        ),
      } as const;
      const plan = await createSwarmTradePlan(request);
      setResult(plan);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to reach the SwarmTrade API.");
    } finally {
      setBusy(false);
    }
  }

  const approved = result?.status === "APPROVED_FOR_SIMULATION";

  return (
    <section className="swarmtrade-panel">
      <div className="swarmtrade-heading">
        <div className="swarmtrade-title-icon"><BrainCircuit size={18} /></div>
        <div>
          <h3>SwarmTrade · Logical Agent Lab</h3>
          <p>Deterministic consensus from up to 500 logical agents with hard risk gates.</p>
        </div>
        <span className="swarmtrade-mode">SIMULATION ONLY</span>
      </div>
      <form className="swarmtrade-form" onSubmit={submit}>
        <div className="swarmtrade-fields">
          <label>Symbol<input value={selectedSymbol} maxLength={40} required onChange={(event) => setSelectedSymbol(event.target.value)} /></label>
          <label>Asset class<select value={assetClass} onChange={(event) => setAssetClass(event.target.value as typeof assetClass)}>
            <option value="equity">Equity</option><option value="option">Option</option><option value="future">Future</option><option value="crypto">Crypto</option><option value="forex">Forex</option>
          </select></label>
          <label>Proposed side<select value={side} onChange={(event) => setSide(event.target.value as typeof side)}>
            <option value="auto">Agent consensus</option><option value="long">Long only</option><option value="short">Short only</option>
          </select></label>
          <label>Entry price<input type="number" min="0.0000001" step="any" required value={fields.entry} onChange={(event) => update("entry", event.target.value)} /></label>
          <label>Stop price<input type="number" min="0.0000001" step="any" required value={fields.stop} onChange={(event) => update("stop", event.target.value)} /></label>
          <label>Target price<input type="number" min="0.0000001" step="any" required value={fields.target} onChange={(event) => update("target", event.target.value)} /></label>
          <label>Capital<input type="number" min="1" step="any" required value={fields.capital} onChange={(event) => update("capital", event.target.value)} /></label>
          <label>Requested risk %<input type="number" min="0.01" max="5" step="0.05" required value={fields.riskPct} onChange={(event) => update("riskPct", event.target.value)} /></label>
          <label>Logical agents (max 500)<input type="number" min="5" max="500" step="5" required value={fields.agents} onChange={(event) => update("agents", event.target.value)} /></label>
          <label>Current daily loss %<input type="number" min="0" max="20" step="0.1" required value={fields.dailyLoss} onChange={(event) => update("dailyLoss", event.target.value)} /></label>
          <label>Open-position risk %<input type="number" min="0" max="3" step="0.1" required value={fields.openRisk} onChange={(event) => update("openRisk", event.target.value)} /></label>
          {(assetClass === "equity" || assetClass === "crypto" || assetClass === "option") && <label>Margin rate (0.01–1)<input type="number" min="0.01" max="1" step="0.01" required value={fields.marginRate} onChange={(event) => update("marginRate", event.target.value)} /></label>
          <label>Max leverage (1–30)<input type="number" min="1" max="30" step="0.5" required value={fields.leverage} onChange={(event) => update("leverage", event.target.value)} /></label>
          <label>Contract / unit multiplier<input type="number" min="0.0000001" step="any" required value={fields.multiplier} onChange={(event) => update("multiplier", event.target.value)} /></label>
          <label>Quantity step<input type="number" min="0.0000001" step="any" required value={fields.unitStep} onChange={(event) => update("unitStep", event.target.value)} /></label>
          {assetClass === "option" && <label>Max loss per contract<input type="number" min="0.0000001" step="any" required value={fields.maxLossPerUnit} onChange={(event) => update("maxLossPerUnit", event.target.value)} /></label>}
          {assetClass === "future" && <>
            <label>Tick size<input type="number" min="0.0000001" step="any" required value={fields.tickSize} onChange={(event) => update("tickSize", event.target.value)} /></label>
            <label>Tick value (account currency)<input type="number" min="0.0000001" step="any" required value={fields.tickValue} onChange={(event) => update("tickValue", event.target.value)} /></label>
            <label>Margin per contract<input type="number" min="0.0000001" step="any" required value={fields.marginPerUnit} onChange={(event) => update("marginPerUnit", event.target.value)} /></label>
          </>}
          {assetClass === "forex" && <>
            <label>Pip size<input type="number" min="0.0000001" step="any" required value={fields.pipSize} onChange={(event) => update("pipSize", event.target.value)} /></label>
            <label>Pip value per unit (account currency)<input type="number" min="0.0000001" step="any" required value={fields.pipValue} onChange={(event) => update("pipValue", event.target.value)} /></label>
            <label>Margin per lot / unit<input type="number" min="0.0000001" step="any" required value={fields.marginPerUnit} onChange={(event) => update("marginPerUnit", event.target.value)} /></label>
          </>}
        </div>
        <div className="swarmtrade-signal-block">
          <strong>Directional input features <small>(-1.0 to +1.0; trend/momentum/reversion/breakout derive from chart bars)</small></strong>
          <div className="swarmtrade-fields swarmtrade-signal-fields">
            {Object.entries(signals).map(([key, value]) => (
              <label key={key}>{key.replace("_", " ")}<input type="number" min="-1" max="1" step="0.1" required value={value} onChange={(event) => setSignals((previous) => ({ ...previous, [key]: event.target.value }))} /></label>
            ))}
          </div>
        </div>
        <p className="swarmtrade-caveat">Features are transparent rules over the selected candles, not trained predictions; sentiment remains neutral unless adjusted manually. Require at least six valid bars for automatic feature initialization. Hard limits: max 1% new-trade risk and 3% aggregate open risk. Supply accurate exchange-specific multipliers, margin and transaction costs. This tool never sends orders.</p>
        <button className="swarmtrade-submit" type="submit" disabled={busy || isLoading || bars.length < 6}>
          {busy ? <LoaderCircle size={15} className="swarmtrade-spin" /> : <BrainCircuit size={15} />}
          {busy ? "Evaluating agents…" : isLoading ? "Waiting for selected market data…" : bars.length < 6 ? "At least 6 chart bars required" : "Run deterministic risk-gated plan"}
        </button>
      </form>
      {error && <div className="swarmtrade-result swarmtrade-error"><ShieldAlert size={16} /><span>{error}</span></div>}
      {result && (
        <div className={`swarmtrade-result ${approved ? "swarmtrade-approved" : "swarmtrade-rejected"}`}>
          {approved ? <ShieldCheck size={18} /> : <ShieldAlert size={18} />}
          <div className="swarmtrade-result-body">
            <div className="swarmtrade-result-title">
              <strong>{result.status.replaceAll("_", " ")}</strong>
              <span>{result.direction.toUpperCase()} · {result.agent_count} logical agents</span>
            </div>
            <p>{result.reason}</p>
            <div className="swarmtrade-result-grid">
              <div><span>Long votes</span><strong>{fmt(result.votes.long)}</strong></div>
              <div><span>Short votes</span><strong>{fmt(result.votes.short)}</strong></div>
              <div><span>Flat votes</span><strong>{fmt(result.votes.flat)}</strong></div>
              <div><span>Consensus score</span><strong>{fmt(result.consensus_score)}</strong></div>
              <div><span>Estimated quantity</span><strong>{fmt(result.sizing?.quantity)}</strong></div>
              <div><span>Estimated risk</span><strong>{fmt(result.risk?.estimated_total_risk)}</strong></div>
              <div><span>Reward / risk</span><strong>{fmt(result.risk?.reward_risk_ratio_after_costs)}</strong></div>
              <div><span>Effective leverage</span><strong>{fmt(result.risk?.effective_leverage)}×</strong></div>
            </div>
            <div className="swarmtrade-execution-label">Execution: {result.execution.mode.replaceAll("_", " ")} · order submitted: no · fill claimed: no</div>
            {result.warnings?.map((warning) => <p className="swarmtrade-warning" key={warning}>{warning}</p>)}
          </div>
        </div>
      )}
    </section>
  );
}

export default SwarmTradePanel;
