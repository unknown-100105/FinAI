import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Activity, CheckCircle2, CircleAlert, LoaderCircle, RefreshCw, ShieldCheck, Wallet } from "lucide-react";
import {
  closePaperPosition,
  createPaperAccount,
  getPaperAccount,
  getPaperLedgerStatus,
  listPaperPositions,
  openPaperPosition,
  type PaperAccountSnapshot,
  type PaperPosition,
  type SwarmTradePlan,
  type SwarmTradeRequest,
} from "../api/swarmtrade";
import "./PaperTradingPanel.css";

const ACCOUNT_STORAGE_KEY = "finai_swarmtrade_paper_account_id";

type Props = {
  symbol: string;
  currentPrice: number | null;
  request: SwarmTradeRequest | null;
  plan: SwarmTradePlan | null;
};

function makeKey(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `finai-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function fmt(value: number | null | undefined, currency?: string): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "—";
  return new Intl.NumberFormat("en-IN", {
    style: currency ? "currency" : "decimal",
    currency: currency || undefined,
    maximumFractionDigits: 2,
  }).format(value);
}

export function PaperTradingPanel({ symbol, currentPrice, request, plan }: Props) {
  const [enabled, setEnabled] = useState<boolean | null>(null);
  const [account, setAccount] = useState<PaperAccountSnapshot | null>(null);
  const [positions, setPositions] = useState<PaperPosition[]>([]);
  const [label, setLabel] = useState("FinAI paper account");
  const [currency, setCurrency] = useState("INR");
  const [initialCapital, setInitialCapital] = useState("100000");
  const [exitPrices, setExitPrices] = useState<Record<string, string>>({});
  const [closeReasons, setCloseReasons] = useState<Record<string, "manual" | "stop" | "target" | "risk_control">>({});
  const [busy, setBusy] = useState(false);
  const [busyPosition, setBusyPosition] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [openKey, setOpenKey] = useState(makeKey);

  const refreshAccount = useCallback(async (accountId: string) => {
    const [snapshot, positionData] = await Promise.all([
      getPaperAccount(accountId),
      listPaperPositions(accountId, "all"),
    ]);
    setAccount(snapshot);
    setPositions(positionData.positions);
  }, []);

  useEffect(() => {
    let active = true;
    async function initialize() {
      try {
        const status = await getPaperLedgerStatus();
        if (!active) return;
        setEnabled(status.enabled);
        if (!status.enabled) return;
        const savedId = window.localStorage.getItem(ACCOUNT_STORAGE_KEY);
        if (savedId) {
          try {
            await refreshAccount(savedId);
          } catch {
            window.localStorage.removeItem(ACCOUNT_STORAGE_KEY);
            if (active) setNotice("Saved paper account could not be loaded. Create a new local account.");
          }
        }
      } catch (cause) {
        if (active) setError(cause instanceof Error ? cause.message : "Unable to read paper ledger status.");
      }
    }
    void initialize();
    return () => { active = false; };
  }, [refreshAccount]);

  const refresh = async () => {
    if (!account) return;
    setBusy(true);
    setError("");
    try {
      await refreshAccount(account.account_id);
      setNotice("Paper account and position history refreshed.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to refresh paper account.");
    } finally {
      setBusy(false);
    }
  };

  async function createAccount(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const created = await createPaperAccount({
        label: label.trim(),
        currency,
        initial_capital: Number(initialCapital),
      });
      window.localStorage.setItem(ACCOUNT_STORAGE_KEY, created.account_id);
      setAccount(created);
      setPositions([]);
      setNotice("Paper account created locally. No brokerage account was connected.");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to create paper account.");
    } finally {
      setBusy(false);
    }
  }

  async function recordPaperEntry() {
    if (!account || !request || plan?.status !== "APPROVED_FOR_SIMULATION") return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const opened = await openPaperPosition({
        account_id: account.account_id,
        idempotency_key: openKey,
        acknowledge_simulation_only: true,
        plan: request,
      });
      await refreshAccount(account.account_id);
      setOpenKey(makeKey());
      setNotice(`Recorded simulation-only entry for ${opened.symbol} (${opened.direction}).`);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to record paper entry.");
    } finally {
      setBusy(false);
    }
  }

  async function closePaperEntry(position: PaperPosition) {
    if (!account) return;
    const rawExit = exitPrices[position.position_id]
      ?? (position.symbol.toUpperCase() === symbol.toUpperCase() && currentPrice != null ? String(currentPrice) : "");
    const exitPrice = Number(rawExit);
    if (!Number.isFinite(exitPrice) || exitPrice <= 0) {
      setError("Enter a finite positive exit price, or select the position's symbol in the Market Terminal.");
      return;
    }
    const reason = closeReasons[position.position_id] || "manual";
    const key = `close:${position.position_id}:${exitPrice}:${reason}`;
    setBusyPosition(position.position_id);
    setError("");
    setNotice("");
    try {
      const closed = await closePaperPosition({
        account_id: account.account_id,
        position_id: position.position_id,
        idempotency_key: key.slice(0, 160),
        exit_price: exitPrice,
        reason,
      });
      await refreshAccount(account.account_id);
      setNotice(`Paper exit recorded. Realized P&L: ${fmt(closed.net_pnl, account.currency)}.`);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unable to record paper exit.");
    } finally {
      setBusyPosition("");
    }
  }

  const approvedForCurrentSymbol = Boolean(
    request && plan?.status === "APPROVED_FOR_SIMULATION"
    && request.symbol.toUpperCase() === symbol.toUpperCase(),
  );

  return (
    <section className="paper-ledger-panel">
      <div className="paper-ledger-heading">
        <span className="paper-ledger-icon"><Wallet size={17} /></span>
        <div className="paper-ledger-heading-copy">
          <h3>Paper Trading Ledger</h3>
          <p>Persistent local simulation · no broker orders or live fills</p>
        </div>
        <span className={`paper-ledger-badge ${enabled ? "enabled" : enabled === false ? "disabled" : ""}`}>
          {enabled === null ? "CHECKING" : enabled ? "ENABLED" : "OPT-IN"}
        </span>
      </div>

      {enabled === false ? (
        <div className="paper-ledger-disabled">
          <CircleAlert size={17} />
          <div>
            <strong>Paper ledger is disabled by default</strong>
            <p>For trusted local testing, set FINAI_ENABLE_SWARMTRADE_PAPER_LEDGER=1 in .env and restart the API. The database path is controlled by FINAI_SWARMTRADE_PAPER_DB. Do not expose this local tool publicly without authentication.</p>
          </div>
        </div>
      ) : enabled === null ? (
        <p className="paper-ledger-muted">Checking local API configuration…</p>
      ) : !account ? (
        <form className="paper-ledger-create" onSubmit={createAccount}>
          <label>Account label<input value={label} maxLength={100} required onChange={(event) => setLabel(event.target.value)} /></label>
          <label>Currency<select value={currency} onChange={(event) => setCurrency(event.target.value)}>
            <option value="INR">INR — Indian rupee</option><option value="USD">USD — US dollar</option><option value="EUR">EUR — euro</option><option value="GBP">GBP — pound sterling</option><option value="SGD">SGD — Singapore dollar</option><option value="JPY">JPY — Japanese yen</option>
          </select></label>
          <label>Starting capital<input type="number" min="1" step="any" value={initialCapital} required onChange={(event) => setInitialCapital(event.target.value)} /></label>
          <button type="submit" disabled={busy || Number(initialCapital) <= 0}>
            {busy ? <LoaderCircle className="paper-ledger-spin" size={14} /> : <Wallet size={14} />}
            Create paper account
          </button>
        </form>
      ) : (
        <>
          <div className="paper-ledger-account-head">
            <div><span>Account</span><strong>{account.label} · {account.currency}</strong><small>{account.account_id}</small></div>
            <button type="button" onClick={refresh} disabled={busy}><RefreshCw size={13} className={busy ? "paper-ledger-spin" : ""} /> Refresh</button>
          </div>
          <div className="paper-ledger-metrics">
            <div><span>Equity*</span><strong>{fmt(account.equity_excluding_unrealized_pnl, account.currency)}</strong></div>
            <div><span>Realized P&L</span><strong className={account.realized_pnl >= 0 ? "positive" : "negative"}>{fmt(account.realized_pnl, account.currency)}</strong></div>
            <div><span>Open-position risk</span><strong>{fmt(account.open_position_risk, account.currency)} · {fmt(account.open_position_risk_pct)}%</strong></div>
            <div><span>Daily realized loss</span><strong>{fmt(account.daily_realized_loss_pct)}%</strong></div>
          </div>
          <p className="paper-ledger-footnote">*Equity excludes unrealized P&L. Daily loss is based on realized paper exits only. Simulated fills/prices are supplied by you, not confirmed by a market or broker.</p>

          <div className="paper-ledger-entry">
            <div className="paper-ledger-entry-title"><ShieldCheck size={15} /><strong>Approved plan to paper position</strong></div>
            <p>{approvedForCurrentSymbol ? `${request?.symbol} · ${plan?.direction.toUpperCase()} · ${plan?.agent_count} logical votes` : "Run a successful risk-gated plan for the currently selected symbol. Any input or quote change invalidates the candidate."}</p>
            <button type="button" onClick={recordPaperEntry} disabled={busy || !approvedForCurrentSymbol}>
              {busy ? <LoaderCircle size={14} className="paper-ledger-spin" /> : <Activity size={14} />}
              Record approved plan as paper entry
            </button>
          </div>

          <div className="paper-ledger-history-head"><strong>Position history</strong><span>{positions.length} record{positions.length === 1 ? "" : "s"}</span></div>
          {positions.length === 0 ? <div className="paper-ledger-empty">No paper positions yet.</div> : (
            <div className="paper-ledger-positions">
              {positions.map((position) => (
                <article className="paper-ledger-position" key={position.position_id}>
                  <div className="paper-ledger-position-head">
                    <div><strong>{position.symbol}</strong><span>{position.direction.toUpperCase()} · {position.asset_class.toUpperCase()} · {fmt(position.quantity)} units</span></div>
                    <span className={`paper-ledger-position-status ${position.status.toLowerCase()}`}>{position.status}</span>
                  </div>
                  <div className="paper-ledger-position-grid">
                    <div><span>Entry</span><strong>{fmt(position.entry_price)}</strong></div>
                    <div><span>Stop</span><strong>{fmt(position.stop_price)}</strong></div>
                    <div><span>Target</span><strong>{fmt(position.target_price)}</strong></div>
                    <div><span>Risk est.</span><strong>{fmt(position.estimated_risk, account.currency)}</strong></div>
                    {position.status === "CLOSED" && <>
                      <div><span>Exit</span><strong>{fmt(position.exit_price)}</strong></div>
                      <div><span>Net P&L</span><strong className={(position.net_pnl ?? 0) >= 0 ? "positive" : "negative"}>{fmt(position.net_pnl, account.currency)}</strong></div>
                    </>}
                  </div>
                  {position.status === "OPEN" && (
                    <div className="paper-ledger-close-row">
                      <label>Exit price<input type="number" min="0.0000001" step="any" value={exitPrices[position.position_id] ?? (position.symbol.toUpperCase() === symbol.toUpperCase() && currentPrice != null ? String(currentPrice) : "")} onChange={(event) => setExitPrices((previous) => ({ ...previous, [position.position_id]: event.target.value }))} placeholder="Current selected-symbol quote" /></label>
                      <label>Close reason<select value={closeReasons[position.position_id] || "manual"} onChange={(event) => setCloseReasons((previous) => ({ ...previous, [position.position_id]: event.target.value as "manual" | "stop" | "target" | "risk_control" }))}>
                        <option value="manual">Manual</option><option value="stop">Stop reached</option><option value="target">Target reached</option><option value="risk_control">Risk control</option>
                      </select></label>
                      <button type="button" onClick={() => void closePaperEntry(position)} disabled={busy || busyPosition === position.position_id}>
                        {busyPosition === position.position_id ? <LoaderCircle size={13} className="paper-ledger-spin" /> : <CheckCircle2 size={13} />}
                        Record exit
                      </button>
                    </div>
                  )}
                </article>
              ))}
            </div>
          )}
        </>
      )}

      {notice && <div className="paper-ledger-notice">{notice}</div>}
      {error && <div className="paper-ledger-error"><CircleAlert size={14} /><span>{error}</span></div>}
    </section>
  );
}

export default PaperTradingPanel;
