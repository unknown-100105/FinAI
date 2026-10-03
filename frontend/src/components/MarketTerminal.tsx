import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  ExternalLink,
  Newspaper,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";
import {
  getMarketAnalytics,
  getMarketHistory,
  getMarketNews,
  getMarketOverview,
  getMarketQuote,
  type MarketBar,
  type MarketNewsItem,
  type MarketOverviewItem,
  type MarketQuote,
} from "../api/market";
import { MarketSearchBox } from "./MarketSearchBox";
import "./MarketTerminal.css";

const ranges = [
  { id: "1D", days: 1, interval: "15m" },
  { id: "5D", days: 5, interval: "30m" },
  { id: "1M", days: 30, interval: "1d" },
  { id: "6M", days: 180, interval: "1d" },
  { id: "1Y", days: 365, interval: "1d" },
  { id: "5Y", days: 1825, interval: "1d" },
] as const;

const quickSymbols = ["TCS", "INFY", "RELIANCE", "HDFCBANK", "NIFTY 50", "SENSEX", "BTC"];

function toNumber(value: number | null | undefined) {
  return Number.isFinite(Number(value)) ? Number(value) : null;
}

function formatPrice(value: number | null | undefined, currency = "INR") {
  const number = toNumber(value);
  if (number === null) return "—";
  try {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: currency || "INR",
      maximumFractionDigits: 2,
    }).format(number);
  } catch {
    return number.toFixed(2);
  }
}

function formatPercent(value: number | null | undefined) {
  const number = toNumber(value);
  if (number === null) return "—";
  return `${number >= 0 ? "+" : ""}${(number * 100).toFixed(2)}%`;
}

function formatRatio(value: number | null | undefined) {
  const number = toNumber(value);
  return number === null ? "—" : number.toFixed(2);
}

function formatVolume(value: number | null | undefined) {
  const number = toNumber(value);
  if (number === null) return "—";
  if (number >= 10000000) return `${(number / 10000000).toFixed(1)}Cr`;
  if (number >= 100000) return `${(number / 100000).toFixed(1)}L`;
  if (number >= 1000) return `${(number / 1000).toFixed(1)}K`;
  return Math.round(number).toString();
}

function rangeDates(days: number) {
  const end = new Date();
  const start = new Date();
  start.setDate(end.getDate() - days);
  return { start: start.toISOString(), end: end.toISOString() };
}

function linePoints(bars: MarketBar[], width: number, height: number) {
  if (!bars.length) return "";
  const closes = bars.map((bar) => bar.close);
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const spread = max - min || 1;
  return bars.map((bar, index) => {
    const x = (index / Math.max(1, bars.length - 1)) * width;
    const y = height - ((bar.close - min) / spread) * height;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
}

function MiniMover({ item }: { item: MarketOverviewItem }) {
  const change = toNumber(item.change_percent);
  const positive = change !== null && change >= 0;
  return (
    <div className="mover-row">
      <div>
        <strong>{item.instrument?.display_name ?? "—"}</strong>
        <span>{item.instrument?.exchange ?? item.instrument?.asset_type}</span>
      </div>
      <div className={positive ? "market-positive" : "market-negative"}>
        {change === null ? "—" : formatPercent(change)}
      </div>
    </div>
  );
}

export function MarketTerminal() {
  const [instrument, setInstrument] = useState("TCS");
  const [range, setRange] = useState("1M");
  const [quote, setQuote] = useState<MarketQuote | null>(null);
  const [bars, setBars] = useState<MarketBar[]>([]);
  const [analytics, setAnalytics] = useState<Record<string, number | null>>({});
  const [gainers, setGainers] = useState<MarketOverviewItem[]>([]);
  const [losers, setLosers] = useState<MarketOverviewItem[]>([]);
  const [news, setNews] = useState<MarketNewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [overviewLoading, setOverviewLoading] = useState(true);
  const [newsLoading, setNewsLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState("");

  const selectedRange = ranges.find((item) => item.id === range) ?? ranges[2];

  const points = useMemo(() => linePoints(bars, 720, 260), [bars]);

  const priceChange = useMemo(() => {
    if (bars.length < 2) return null;
    const first = bars[0].close;
    const last = bars[bars.length - 1].close;
    return first ? last / first - 1 : null;
  }, [bars]);

  const loadMarket = async () => {
    setLoading(true);
    setError("");
    setQuote(null);
    setBars([]);
    setAnalytics({});

    try {
      const dates = rangeDates(selectedRange.days);
      const [quoteResult, historyResult, analyticsResult] = await Promise.all([
        getMarketQuote(instrument),
        getMarketHistory(instrument, dates.start, dates.end, selectedRange.interval),
        getMarketAnalytics(instrument, dates.start, dates.end, selectedRange.interval),
      ]);
      setQuote(quoteResult.quote);
      setBars(historyResult.bars);
      setAnalytics(analyticsResult.analytics);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Market data is unavailable.");
    } finally {
      setLoading(false);
    }
  };

  const loadOverview = async () => {
    setOverviewLoading(true);
    try {
      const overview = await getMarketOverview();
      setGainers(overview.gainers);
      setLosers(overview.losers);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Market movers are unavailable.");
    } finally {
      setOverviewLoading(false);
    }
  };

  const loadNews = async () => {
    setNewsLoading(true);
    try {
      const result = await getMarketNews(instrument, 8);
      setNews(result.articles);
    } catch {
      setNews([]);
    } finally {
      setNewsLoading(false);
    }
  };

  useEffect(() => { void loadMarket(); }, [instrument, range]);
  useEffect(() => { void loadOverview(); }, []);
  useEffect(() => { void loadNews(); }, [instrument]);

  const positive = priceChange !== null && priceChange >= 0;
  const currency = quote?.currency || "INR";

  return (
    <section className="market-terminal">
      <div className="market-header">
        <div>
          <div className="market-kicker"><BarChart3 size={14} /> Market intelligence</div>
          <h2>Live market terminal</h2>
          <p>Searchable instruments, multi-horizon charts, quantitative analytics, movers and instrument-specific news.</p>
        </div>
        <button
          className="market-refresh"
          type="button"
          onClick={() => { void loadMarket(); void loadOverview(); void loadNews(); }}
          disabled={loading}
        >
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
                  <button type="button" key={symbol} onClick={() => setInstrument(symbol)} className={instrument === symbol ? "active" : ""}>
                    {symbol}
                  </button>
                ))}
              </div>
            </div>
            <div className="market-control-groups">
              <div className="control-group">
                <span>Range</span>
                <div className="range-tabs">
                  {ranges.map((item) => (
                    <button key={item.id} type="button" className={range === item.id ? "active" : ""} onClick={() => setRange(item.id)}>
                      {item.id}
                    </button>
                  ))}
                </div>
              </div>
              <div className="control-group">
                <span>Interval</span>
                <div className="range-tabs interval-tabs">
                  {["1m", "5m", "15m", "30m", "1h", "1d", "1wk"].map((value) => (
                    <button
                      key={value}
                      type="button"
                      className={interval === value ? "active" : ""}
                      disabled={!intradayAllowed && !["1d", "1wk"].includes(value)}
                      onClick={() => setInterval(value)}
                    >
                      {value}
                    </button>
                  ))}
                </div>
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
                <div><span>Last price</span><strong>{formatPrice(quote.price, currency)}</strong></div>
                <div><span>Period change</span><strong className={positive ? "market-positive" : "market-negative"}>{formatPercent(priceChange)}</strong></div>
                <div><span>Day range</span><strong>{formatPrice(quote.low, currency)} — {formatPrice(quote.high, currency)}</strong></div>
                <div><span>Volume</span><strong>{formatVolume(quote.volume)}</strong></div>
              </div>
            </>
          )}

          <div className="chart-card">
            <div className="chart-head">
              <div><span>{instrument}</span><small>{lastUpdated ? `Updated ${lastUpdated} · ${interval}` : "Loading market feed"}</small></div>
              <div className="chart-badge"><Activity size={13} /> {quote?.source ?? "market feed"}</div>
            </div>
            <div className="chart-wrap">
              {bars.length > 1 ? (
                <svg viewBox="0 0 720 260" preserveAspectRatio="none" role="img" aria-label={`${instrument} historical price chart`}>
                  <polyline points={points} fill="none" stroke="currentColor" strokeWidth="3" vectorEffect="non-scaling-stroke" className={positive ? "chart-line-positive" : "chart-line-negative"} />
                </svg>
              ) : (
                <div className="chart-empty">{loading ? "Loading price history…" : "No historical data available for this timeframe."}</div>
              )}
            </div>
          </div>

          <div className="analytics-grid">
            {[
              ["SMA 20", formatPrice(analytics.sma_20, currency)],
              ["SMA 50", formatPrice(analytics.sma_50, currency)],
              ["EMA 20", formatPrice(analytics.ema_20, currency)],
              ["RSI 14", formatRatio(analytics.rsi_14)],
              ["Annualized volatility", formatPercent(analytics.annualized_volatility)],
              ["Maximum drawdown", formatPercent(analytics.maximum_drawdown)],
            ].map(([label, value]) => (
              <div key={label} className="analytics-card">
                <span>{label}</span>
                <strong>{value}</strong>
                <small>Calculated from the selected history window</small>
              </div>
            ))}
          </div>
        </div>

        <aside className="market-side">
          <div className="market-side-card">
            <div className="side-card-heading"><span>Top gainers</span><ArrowUpRight size={15} /></div>
            {overviewLoading ? <div className="news-loading">Loading movers…</div> : gainers.length ? gainers.map((item) => <MiniMover key={item.instrument.instrument_id} item={item} />) : <div className="news-loading">No movers returned.</div>}
          </div>

          <div className="market-side-card">
            <div className="side-card-heading"><span>Top losers</span><ArrowDownRight size={15} /></div>
            {overviewLoading ? <div className="news-loading">Loading movers…</div> : losers.length ? losers.map((item) => <MiniMover key={item.instrument.instrument_id} item={item} />) : <div className="news-loading">No movers returned.</div>}
          </div>

          <div className="market-side-card">
            <div className="side-card-heading"><span>{instrument} news</span><Newspaper size={15} /></div>
            {newsLoading ? <div className="news-loading">Fetching headlines…</div> : news.length ? news.map((item, index) => (
              <a key={`${item.title}-${index}`} className="news-item" href={item.link || "#"} target="_blank" rel="noreferrer">
                <div><strong>{item.title}</strong><span>{item.publisher || "Financial news"} · {item.published_at || "Latest"}</span></div>
                <ExternalLink size={13} />
              </a>
            )) : <div className="news-loading">No instrument-specific news returned.</div>}
          </div>

          <div className="market-side-card market-evidence-card">
            <div className="side-card-heading"><span>Data discipline</span><ShieldCheck size={15} /></div>
            <p>Market values are provider snapshots, not guaranteed execution prices. Verify exchange availability, timestamp and liquidity before acting.</p>
          </div>
        </aside>
      </div>
    </section>
  );
}

export default MarketTerminal;
