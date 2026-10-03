import { useEffect, useState } from "react";
import {
  Activity, ArrowDownRight, ArrowUpRight, BarChart3, ExternalLink,
  Newspaper, RefreshCw, ShieldCheck,
} from "lucide-react";
import {
  getMarketAnalytics, getMarketHistory, getMarketNews, getMarketOverview,
  getMarketQuote, type MarketBar, type MarketNewsItem,
  type MarketOverviewItem, type MarketQuote,
} from "../api/market";
import { MarketSearchBox } from "./MarketSearchBox";
import { CandleChart } from "./CandleChart";
import "./MarketTerminal.css";

const ranges = [
  { id: "1D", days: 1, interval: "15m" },
  { id: "5D", days: 5, interval: "30m" },
  { id: "1M", days: 30, interval: "1d" },
  { id: "3M", days: 90, interval: "1d" },
  { id: "6M", days: 180, interval: "1d" },
  { id: "YTD", days: 365, interval: "1d" },
  { id: "1Y", days: 365, interval: "1d" },
  { id: "5Y", days: 1825, interval: "1d" },
  { id: "MAX", days: 3650, interval: "1d" },
] as const;

const intervals = ["1m", "5m", "15m", "30m", "1h", "1d", "1wk"] as const;
const quickSymbols = [
  "TCS", "INFY", "RELIANCE", "HDFCBANK", "ICICIBANK", "SBIN",
  "ITC", "LT", "NIFTY 50", "SENSEX", "BTC", "ETH",
];

function finite(value: unknown): number | null {
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

function money(value: unknown, currency = "INR") {
  const n = finite(value);
  if (n === null) return "—";
  try {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency,
      maximumFractionDigits: 2,
    }).format(n);
  } catch {
    return n.toFixed(2);
  }
}

function percent(value: unknown) {
  const n = finite(value);
  return n === null ? "—" : `${n >= 0 ? "+" : ""}${(n * 100).toFixed(2)}%`;
}

function volume(value: unknown) {
  const n = finite(value);
  if (n === null) return "—";
  if (n >= 1e7) return `${(n / 1e7).toFixed(1)}Cr`;
  if (n >= 1e5) return `${(n / 1e5).toFixed(1)}L`;
  if (n >= 1e3) return `${(n / 1e3).toFixed(1)}K`;
  return Math.round(n).toString();
}

function datesFor(days: number) {
  const end = new Date();
  const start = new Date();
  start.setDate(end.getDate() - days);
  return { start: start.toISOString(), end: end.toISOString() };
}

function MiniMover({ item }: { item: MarketOverviewItem }) {
  const change = finite(item.change_percent);
  return (
    <div className="mover-row">
      <div>
        <strong>{item.instrument?.display_name ?? "—"}</strong>
        <span>{item.instrument?.exchange ?? item.instrument?.asset_type ?? "market"}</span>
      </div>
      <div className={change !== null && change >= 0 ? "market-positive" : "market-negative"}>
        {percent(change)}
      </div>
    </div>
  );
}

export function MarketTerminal() {
  const [instrument, setInstrument] = useState("TCS");
  const [range, setRange] = useState("1M");
  const [interval, setInterval] = useState("1d");
  const [quote, setQuote] = useState<MarketQuote | null>(null);
  const [bars, setBars] = useState<MarketBar[]>([]);
  const [analytics, setAnalytics] = useState<Record<string, number | null>>({});
  const [gainers, setGainers] = useState<MarketOverviewItem[]>([]);
  const [losers, setLosers] = useState<MarketOverviewItem[]>([]);
  const [news, setNews] = useState<MarketNewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [sideLoading, setSideLoading] = useState(true);
  const [error, setError] = useState("");

  const selectedRange = ranges.find((item) => item.id === range) ?? ranges[2];
  const intervalAllowed = (value: string) => {
    if (value === "1m" || value === "2m" || value === "5m") return selectedRange.days <= 7;
    if (value === "15m" || value === "30m" || value === "1h") return selectedRange.days <= 60;
    return true;
  };

  useEffect(() => {
    setInterval(selectedRange.interval);
  }, [range]);

  const load = async () => {
    setLoading(true);
    setError("");
    setQuote(null);
    setBars([]);
    setAnalytics({});
    const window = datesFor(selectedRange.days);

    try {
      const [quoteResult, historyResult, analyticsResult] = await Promise.allSettled([
        getMarketQuote(instrument),
        getMarketHistory(instrument, window.start, window.end, interval),
        getMarketAnalytics(instrument, window.start, window.end, interval),
      ]);

      const failures: string[] = [];
      if (quoteResult.status === "fulfilled") {
        setQuote(quoteResult.value.quote);
      } else {
        setQuote(null);
        failures.push("quote");
      }

      if (historyResult.status === "fulfilled") {
        setBars(historyResult.value.bars);
      } else {
        setBars([]);
        failures.push("history");
      }

      if (analyticsResult.status === "fulfilled") {
        setAnalytics(analyticsResult.value.analytics);
      } else {
        setAnalytics({});
        failures.push("analytics");
      }

      if (failures.length === 3) {
        const firstError = quoteResult.status === "rejected" ? quoteResult.reason : "Market data unavailable.";
        throw firstError instanceof Error ? firstError : new Error("Market data unavailable.");
      }

      if (failures.length > 0) {
        setError(`Partial market feed: ${failures.join(", ")} unavailable; available charts/data remain visible.`);
      }
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Market data unavailable.");
    } finally {
      setLoading(false);
    }
  };

  const loadSide = async () => {
    setSideLoading(true);
    try {
      const [overview, headlines] = await Promise.all([
        getMarketOverview(),
        getMarketNews(instrument, 8),
      ]);
      setGainers(overview.gainers);
      setLosers(overview.losers);
      setNews(headlines.articles);
    } catch {
      setNews([]);
    } finally {
      setSideLoading(false);
    }
  };

  useEffect(() => { void load(); }, [instrument, range, interval]);
  useEffect(() => {
    const timer = window.setInterval(() => { void load(); }, interval === "1m" || interval === "5m" || interval === "15m" || interval === "30m" ? 15000 : 60000);
    return () => window.clearInterval(timer);
  }, [instrument, range, interval]);
  useEffect(() => { void loadSide(); }, [instrument]);

  const firstClose = bars.length ? bars[0].close : null;
  const lastClose = bars.length ? bars[bars.length - 1].close : null;
  const periodChange = firstClose ? (lastClose ?? firstClose) / firstClose - 1 : null;
  const positive = periodChange !== null && periodChange >= 0;
  const currency = quote?.currency || "INR";

  return (
    <section className="market-terminal">
      <div className="market-header">
        <div>
          <div className="market-kicker"><BarChart3 size={14} /> Market intelligence</div>
          <h2>Market & crypto terminal</h2>
          <p>Search instruments, inspect intraday or long-horizon price action, calculate indicators and open instrument-specific news.</p>
        </div>
        <button className="market-refresh" type="button" onClick={() => { void load(); void loadSide(); }} disabled={loading}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {error && <div className="market-error">{error}</div>}

      <div className="market-layout">
        <div className="market-main">
          <div className="instrument-toolbar market-toolbar-enhanced">
            <div className="market-search-stack">
              <MarketSearchBox value={instrument} onSelect={setInstrument} />
              <div className="market-quick-list">
                {quickSymbols.map((symbol) => (
                  <button key={symbol} type="button" className={instrument === symbol ? "active" : ""} onClick={() => setInstrument(symbol)}>
                    {symbol}
                  </button>
                ))}
              </div>
            </div>
            <div className="market-control-groups">
              <div className="control-group">
                <span>Range</span>
                <div className="range-tabs">{ranges.map((item) => (
                  <button key={item.id} type="button" className={range === item.id ? "active" : ""} onClick={() => setRange(item.id)}>{item.id}</button>
                ))}</div>
              </div>
              <div className="control-group">
                <span>Interval</span>
                <div className="range-tabs interval-tabs">{intervals.map((value) => (
                  <button key={value} type="button" className={interval === value ? "active" : ""} disabled={!intervalAllowed(value)} onClick={() => setInterval(value)}>{value}</button>
                ))}</div>
              </div>
            </div>
          </div>

          {quote && (
            <>
              <div className="market-instrument-meta">
                <div>
                  <span>{quote.source || "provider"} · {quote.timestamp ? new Date(quote.timestamp).toLocaleString() : "latest available"}</span>
                  <strong>{instrument}</strong>
                </div>
                <span className="market-live-chip"><span /> Provider snapshot</span>
              </div>
              <div className="quote-strip">
                <div><span>Last price</span><strong>{money(quote.price, currency)}</strong></div>
                <div><span>Period change</span><strong className={positive ? "market-positive" : "market-negative"}>{percent(periodChange)}</strong></div>
                <div><span>High / low</span><strong>{money(quote.high, currency)} — {money(quote.low, currency)}</strong></div>
                <div><span>Volume</span><strong>{volume(quote.volume)}</strong></div>
              </div>
            </>
          )}

          <div className="chart-card">
            <div className="chart-head">
              <div><span>{instrument}</span><small>{loading ? "Loading…" : `${bars.length} bars · ${interval}`}</small></div>
              <div className="chart-badge"><Activity size={13} /> {quote?.source ?? "market feed"}</div>
            </div>
            <div className="chart-wrap chart-grid">
              {loading ? <div className="chart-empty">Loading OHLC candles…</div> : <CandleChart bars={bars} height={310} showVolume={true} />}
            </div>
            <div className="chart-footer">
              <span>{bars[0]?.timestamp ? new Date(bars[0].timestamp).toLocaleString() : "—"}</span>
              <span>{bars.at(-1)?.timestamp ? new Date(bars.at(-1)!.timestamp).toLocaleString() : "—"}</span>
            </div>
          </div>

          <div className="analytics-grid">
            {[
              ["SMA 20", money(analytics.sma_20, currency)],
              ["SMA 50", money(analytics.sma_50, currency)],
              ["EMA 20", money(analytics.ema_20, currency)],
              ["RSI 14", finite(analytics.rsi_14)?.toFixed(2) ?? "—"],
              ["Annualized volatility", percent(analytics.annualized_volatility)],
              ["Maximum drawdown", percent(analytics.maximum_drawdown)],
            ].map(([label, value]) => (
              <div className="analytics-card" key={label}><span>{label}</span><strong>{value}</strong><small>Calculated from selected bars</small></div>
            ))}
          </div>
        </div>

        <aside className="market-side">
          <div className="market-side-card">
            <div className="side-card-heading"><span>Top gainers</span><ArrowUpRight size={15} /></div>
            {sideLoading ? <div className="news-loading">Loading…</div> : gainers.map((item) => <MiniMover key={item.instrument.instrument_id} item={item} />)}
          </div>
          <div className="market-side-card">
            <div className="side-card-heading"><span>Top losers</span><ArrowDownRight size={15} /></div>
            {sideLoading ? <div className="news-loading">Loading…</div> : losers.map((item) => <MiniMover key={item.instrument.instrument_id} item={item} />)}
          </div>
          <div className="market-side-card news-card">
            <div className="side-card-heading"><span>{instrument} news</span><Newspaper size={15} /></div>
            {sideLoading ? <div className="news-loading">Fetching headlines…</div> : news.length ? news.map((item, index) => (
              <a key={item.title + index} className="news-item" href={item.link || "#"} target="_blank" rel="noreferrer">
                <div><strong>{item.title}</strong><span>{item.publisher || "Financial news"} · {item.published_at || "latest"}</span></div>
                <ExternalLink size={13} />
              </a>
            )) : <div className="news-loading">No instrument-specific news returned.</div>}
          </div>
          <div className="market-side-card market-evidence-card">
            <div className="side-card-heading"><span>Data discipline</span><ShieldCheck size={15} /></div>
            <p>Values are provider snapshots. Intraday stock data is bounded by provider retention; when an exchange is closed, the chart uses the latest available session and keeps the timestamp visible.</p>
          </div>
        </aside>
      </div>
    </section>
  );
}

export default MarketTerminal;
