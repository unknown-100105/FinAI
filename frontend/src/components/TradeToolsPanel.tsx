import { useEffect, useMemo, useState } from "react";
import { BellRing, Bookmark, Calculator, Plus, Trash2, TriangleAlert } from "lucide-react";

type PriceAlert = { id: string; symbol: string; target: number; direction: "above" | "below" };
type PositionDraft = {
  symbol: string;
  entry: string;
  entrySource: "quote" | "manual";
  stop: string;
  target: string;
};
const WATCHLIST_KEY = "finai.trade.watchlist.v1";
const ALERTS_KEY = "finai.trade.alerts.v1";

function readStored<T>(key: string, fallback: T): T {
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

function readWatchlist(): string[] {
  const stored = readStored<unknown>(WATCHLIST_KEY, []);
  if (!Array.isArray(stored)) return [];
  return [...new Set(stored
    .filter((value): value is string => typeof value === "string")
    .map((value) => value.trim().toUpperCase())
    .filter(Boolean))].slice(-30);
}

function readAlerts(): PriceAlert[] {
  const stored = readStored<unknown>(ALERTS_KEY, []);
  if (!Array.isArray(stored)) return [];
  return stored.filter((value): value is PriceAlert => {
    if (!value || typeof value !== "object") return false;
    const item = value as Record<string, unknown>;
    return typeof item.id === "string"
      && typeof item.symbol === "string"
      && item.symbol.trim().length > 0
      && typeof item.target === "number"
      && Number.isFinite(item.target)
      && item.target > 0
      && (item.direction === "above" || item.direction === "below");
  }).slice(-50);
}

function numeric(value: string): number | null {
  if (!value.trim()) return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function format(value: number, currency: string) {
  try {
    return new Intl.NumberFormat("en-IN", { style: "currency", currency, maximumFractionDigits: 2 }).format(value);
  } catch {
    return value.toFixed(2);
  }
}

export function TradeToolsPanel({ symbol, price, currency = "INR" }: { symbol: string; price: number | null; currency?: string }) {
  const [watchlist, setWatchlist] = useState<string[]>(() => readWatchlist());
  const [alerts, setAlerts] = useState<PriceAlert[]>(() => readAlerts());
  const [watchInput, setWatchInput] = useState("");
  const [alertTarget, setAlertTarget] = useState("");
  const [alertDirection, setAlertDirection] = useState<"above" | "below">("above");
  const [riskBudget, setRiskBudget] = useState("1000");
  const [side, setSide] = useState<"long" | "short">("long");
  const [positionDraft, setPositionDraft] = useState<PositionDraft>(() => ({
    symbol,
    entry: price === null ? "" : String(price),
    entrySource: "quote",
    stop: "",
    target: "",
  }));
  const position = positionDraft.symbol === symbol
    ? positionDraft
    : { symbol, entry: price === null ? "" : String(price), entrySource: "quote" as const, stop: "", target: "" };
  const entry = position.entrySource === "manual"
    ? position.entry
    : price === null ? position.entry : String(price);
  const stop = position.stop;
  const target = position.target;
  const updatePosition = (patch: Partial<PositionDraft>) => {
    setPositionDraft({ ...position, ...patch, symbol });
  };

  useEffect(() => {
    try { window.localStorage.setItem(WATCHLIST_KEY, JSON.stringify(watchlist)); } catch { /* Storage may be disabled. */ }
  }, [watchlist]);

  useEffect(() => {
    try { window.localStorage.setItem(ALERTS_KEY, JSON.stringify(alerts)); } catch { /* Storage may be disabled. */ }
  }, [alerts]);

  const entryValue = numeric(entry);
  const stopValue = numeric(stop);
  const targetValue = numeric(target);
  const budgetValue = numeric(riskBudget);
  const riskPerUnit = entryValue !== null && stopValue !== null
    ? (side === "long" ? entryValue - stopValue : stopValue - entryValue)
    : null;
  const rewardPerUnit = entryValue !== null && targetValue !== null
    ? (side === "long" ? targetValue - entryValue : entryValue - targetValue)
    : null;
  const quantity = riskPerUnit !== null && riskPerUnit > 0 && budgetValue !== null && budgetValue > 0
    ? Math.floor(budgetValue / riskPerUnit)
    : null;
  const rewardRisk = useMemo(() => {
    if (riskPerUnit === null || rewardPerUnit === null || riskPerUnit <= 0 || rewardPerUnit <= 0) return null;
    return rewardPerUnit / riskPerUnit;
  }, [riskPerUnit, rewardPerUnit]);

  const addWatch = () => {
    const next = watchInput.trim().toUpperCase();
    if (!next) return;
    setWatchlist((current) => current.includes(next) ? current : [...current, next].slice(-30));
    setWatchInput("");
  };

  const addAlert = () => {
    const nextTarget = numeric(alertTarget);
    if (nextTarget === null || nextTarget <= 0) return;
    setAlerts((current) => [...current, { id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`, symbol: symbol.toUpperCase(), target: nextTarget, direction: alertDirection }].slice(-50));
    setAlertTarget("");
  };

  const activeAlerts = alerts.filter((alert) => alert.symbol === symbol.toUpperCase());
  const triggered = activeAlerts.filter((alert) => price !== null && (alert.direction === "above" ? price >= alert.target : price <= alert.target));

  return (
    <section className="trade-tools" aria-label="Trade planning tools">
      <div className="trade-tools-heading">
        <div><span className="trade-tools-kicker">WORKSPACE TOOLS</span><h3>Trade planner</h3></div>
        <span className="trade-tools-symbol">{symbol}</span>
      </div>
      <div className="trade-tools-grid">
        <div className="trade-tool-card">
          <div className="trade-tool-title"><Bookmark size={15} /><strong>Watchlist</strong></div>
          <form className="trade-inline-form" onSubmit={(event) => { event.preventDefault(); addWatch(); }}>
            <input aria-label="Add symbol to watchlist" value={watchInput} onChange={(event) => setWatchInput(event.target.value)} placeholder="Add symbol (e.g. INFY)" maxLength={24} />
            <button type="submit" aria-label="Add to watchlist" disabled={!watchInput.trim()}><Plus size={15} /></button>
          </form>
          {watchlist.length ? <div className="trade-watchlist">{watchlist.map((item) => (
            <div className={item === symbol.toUpperCase() ? "trade-watch-row selected" : "trade-watch-row"} key={item}>
              <button type="button" onClick={() => { window.dispatchEvent(new CustomEvent("finai:market-symbol", { detail: item })); }} title={`Select ${item} in the market terminal`}>{item}</button>
              <button type="button" aria-label={`Remove ${item}`} onClick={() => setWatchlist((current) => current.filter((value) => value !== item))}><Trash2 size={13} /></button>
            </div>
          ))}</div> : <p className="trade-tool-empty">Your saved symbols appear here on this browser.</p>}
        </div>

        <div className="trade-tool-card">
          <div className="trade-tool-title"><BellRing size={15} /><strong>Price alerts</strong></div>
          <div className="trade-alert-form">
            <select aria-label="Alert condition" value={alertDirection} onChange={(event) => setAlertDirection(event.target.value as "above" | "below")}>
              <option value="above">Price reaches / exceeds</option><option value="below">Price reaches / falls below</option>
            </select>
            <div className="trade-inline-form">
              <input aria-label="Alert price" type="number" min="0.000001" step="any" value={alertTarget} onChange={(event) => setAlertTarget(event.target.value)} placeholder="Target price" />
              <button type="button" onClick={addAlert} disabled={numeric(alertTarget) === null || (numeric(alertTarget) ?? 0) <= 0} aria-label="Add price alert"><Plus size={15} /></button>
            </div>
          </div>
          {triggered.length > 0 && <div className="trade-alert-triggered"><TriangleAlert size={14} /> {triggered.length} alert condition(s) met at the latest fetched quote.</div>}
          {activeAlerts.length ? <div className="trade-alert-list">{activeAlerts.map((alert) => (
            <div className="trade-alert-row" key={alert.id}>
              <span>{alert.direction === "above" ? "≥" : "≤"} {format(alert.target, currency)}</span>
              <button type="button" aria-label="Delete price alert" onClick={() => setAlerts((current) => current.filter((item) => item.id !== alert.id))}><Trash2 size={13} /></button>
            </div>
          ))}</div> : <p className="trade-tool-empty">Alerts are checked when this terminal fetches a quote; they are not push notifications.</p>}
        </div>

        <div className="trade-tool-card trade-position-card">
          <div className="trade-tool-title"><Calculator size={15} /><strong>Position sizing</strong></div>
          <p className="trade-tool-hint">Estimate units from a fixed risk budget and stop distance.</p>
          <div className="trade-calculator-fields">
            <label>Position side<select value={side} onChange={(event) => setSide(event.target.value as "long" | "short")}><option value="long">Long (buy)</option><option value="short">Short (sell)</option></select></label>
            <label>Entry price<input type="number" min="0" step="any" value={entry} onChange={(event) => updatePosition({ entry: event.target.value, entrySource: "manual" })} placeholder="Entry" /></label>
            <label>Stop price<input type="number" min="0" step="any" value={stop} onChange={(event) => updatePosition({ stop: event.target.value })} placeholder="Stop" /></label>
            <label>Target price<input type="number" min="0" step="any" value={target} onChange={(event) => updatePosition({ target: event.target.value })} placeholder="Target (optional)" /></label>
            <label>Max risk<input type="number" min="0" step="any" value={riskBudget} onChange={(event) => setRiskBudget(event.target.value)} placeholder="Risk budget" /></label>
          </div>
          <div className="trade-position-result">
            <div><span>Estimated quantity</span><strong>{quantity === null ? "—" : quantity.toLocaleString("en-IN")}</strong></div>
            <div><span>Risk per unit</span><strong>{riskPerUnit === null || riskPerUnit <= 0 ? "—" : format(riskPerUnit, currency)}</strong></div>
            <div><span>Reward / risk</span><strong>{rewardRisk === null ? "—" : `${rewardRisk.toFixed(2)} : 1`}</strong></div>
          </div>
          <p className="trade-tool-disclaimer">Planning estimate only. Excludes fees, taxes, slippage, lot sizes, liquidity and margin rules; it does not place orders or recommend a trade.</p>
        </div>
      </div>
    </section>
  );
}

export default TradeToolsPanel;
