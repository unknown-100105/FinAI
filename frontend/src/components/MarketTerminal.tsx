import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  Clock3,
  ExternalLink,
  Newspaper,
  RefreshCw,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import {
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

const instruments = [
  "NIFTY 50",
  "SENSEX",
  "TCS",
  "INFY",
  "RELIANCE",
  "HDFCBANK",
  "ICICIBANK",
  "SBIN",
  "ITC",
  "LT",
  "WIPRO",
  "BHARTIARTL",
  "MARUTI",
  "AXISBANK",
  "Bitcoin",
  "Ethereum",
  "Gold",
  "Silver",
  "USD/INR",
  "EUR/INR",
];

const ranges = [
  { id: "1M", days: 30 },
  { id: "3M", days: 90 },
  { id: "6M", days: 180 },
  { id: "1Y", days: 365 },
];

function toNumber(value: number | null | undefined) {
  return Number.isFinite(Number(value)) ? Number(value) : null;
}

function formatPrice(value: number | null | undefined, currency = "INR") {
  const number = toNumber(value);
  if (number === null) return "—";

  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(number);
}

function formatPercent(value: number | null | undefined) {
  const number = toNumber(value);
  if (number === null) return "—";

  return `${number >= 0 ? "+" : ""}${(number * 100).toFixed(2)}%`;
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
  return {
    start: start.toISOString(),
    end: end.toISOString(),
  };
}

function linePoints(bars: MarketBar[], width: number, height: number) {
  if (!bars.length) return "";

  const closes = bars.map((bar) => bar.close);
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const spread = max - min || 1;

  return bars
    .map((bar, index) => {
      const x = (index / Math.max(1, bars.length - 1)) * width;
      const y = height - ((bar.close - min) / spread) * height;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
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
  const [gainers, setGainers] = useState<MarketOverviewItem[]>([]);
  const [losers, setLosers] = useState<MarketOverviewItem[]>([]);
  const [news, setNews] = useState<MarketNewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [newsLoading, setNewsLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState("");

  const selectedDays =
    ranges.find((item) => item.id === range)?.days ?? 30;

  const points = useMemo(
    () => linePoints(bars, 720, 260),
    [bars],
  );

  const priceChange = useMemo(() => {
    if (bars.length < 2) return null;
    const first = bars[0].close;
    const last = bars[bars.length - 1].close;
    if (!first) return null;
    return last / first - 1;
  }, [bars]);

  const loadMarket = async () => {
    setLoading(true);
    setError("");

    try {
      const dates = rangeDates(selectedDays);
      const [quoteResult, historyResult, overviewResult] =
        await Promise.all([
          getMarketQuote(instrument),
          getMarketHistory(instrument, dates.start, dates.end),
          getMarketOverview(),
        ]);

      setQuote(quoteResult.quote);
      setBars(historyResult.bars);
      setGainers(overviewResult.gainers);
      setLosers(overviewResult.losers);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Market data is unavailable.",
      );
    } finally {
      setLoading(false);
    }
  };

  const loadNews = async () => {
    setNewsLoading(true);
    try {
      const result = await getMarketNews("Indian stock market", 8);
      setNews(result.articles);
    } catch {
      setNews([]);
    } finally {
      setNewsLoading(false);
    }
  };

  useEffect(() => {
    void loadMarket();
  }, [instrument, range]);

  useEffect(() => {
    void loadNews();
  }, []);

  const positive = priceChange !== null && priceChange >= 0;

  return (
    <section className="market-terminal">
      <div className="market-header">
        <div>
          <div className="market-kicker">
            <BarChart3 size={14} />
            Market intelligence
          </div>
          <h2>Live market terminal</h2>
          <p>Quotes, historical price action, movers, analytics, and financial news in one view.</p>
        </div>

        <button
          className="market-refresh"
          type="button"
          onClick={() => {
            void loadMarket();
            void loadNews();
          }}
          disabled={loading}
        >
          <RefreshCw size={14} />
          Refresh
        </button>
      </div>

      {error && <div className="market-error">{error}</div>}

      <div className="market-layout">
        <div className="market-main">
          <div className="instrument-toolbar">
            <MarketSearchBox
              value={instrument}
              onSelect={(symbol) => setInstrument(symbol)}
            />

            <div className="range-tabs">
              {ranges.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  className={range === item.id ? "active" : ""}
                  onClick={() => setRange(item.id)}
                >
                  {item.id}
                </button>
              ))}
            </div>
          </div>

          <div className="quote-strip">
            <div>
              <span>Last price</span>
              <strong>{formatPrice(quote?.price, quote?.currency || "INR")}</strong>
            </div>
            <div>
              <span>Period change</span>
              <strong className={positive ? "market-positive" : "market-negative"}>
                {formatPercent(priceChange)}
              </strong>
            </div>
            <div>
              <span>Day range</span>
              <strong>
                {formatPrice(quote?.low, quote?.currency || "INR")} —{" "}
                {formatPrice(quote?.high, quote?.currency || "INR")}
              </strong>
            </div>
            <div>
              <span>Volume</span>
              <strong>{formatVolume(quote?.volume)}</strong>
            </div>
          </div>

          <div className="chart-card">
            <div className="chart-head">
              <div>
                <span>{instrument}</span>
                <small>{lastUpdated ? `Updated ${lastUpdated}` : "Loading market feed"}</small>
              </div>
              <div className="chart-badge">
                <Activity size={13} />
                {quote?.source ?? "market feed"}
              </div>
            </div>

            <div className="chart-wrap">
              {bars.length > 1 ? (
                <svg viewBox="0 0 720 260" preserveAspectRatio="none" role="img" aria-label={`${instrument} historical price chart`}>
                  <defs>
                    <linearGradient id="finaiChartFill" x1="0" x2="0" y1="0" y2="1">
                      <stop offset="0%" stopOpacity="0.26" />
                      <stop offset="100%" stopOpacity="0" />
                    </linearGradient>
                  </defs>
                  <polyline
                    points={points}
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="3"
                    vectorEffect="non-scaling-stroke"
                    className={positive ? "chart-line-positive" : "chart-line-negative"}
                  />
                </svg>
              ) : (
                <div className="chart-empty">
                  {loading ? "Loading price history…" : "No historical data available for this range."}
                </div>
              )}
            </div>
          </div>

          <div className="analytics-strip">
            <div>
              <span><TrendingUp size={13} /> SMA / EMA</span>
              <strong>
                {bars.length >= 20 ? "20-day indicators ready" : "Need 20+ sessions"}
              </strong>
            </div>
            <div>
              <span><TrendingDown size={13} /> Risk view</span>
              <strong>Volatility · drawdown · RSI</strong>
            </div>
            <div>
              <span><Clock3 size={13} /> Data source</span>
              <strong>{quote?.source ?? "—"}</strong>
            </div>
          </div>
        </div>

        <aside className="market-side">
          <div className="market-side-card">
            <div className="side-card-heading">
              <span>Top gainers</span>
              <ArrowUpRight size={15} />
            </div>
            {gainers.map((item) => (
              <MiniMover key={item.instrument.instrument_id} item={item} />
            ))}
          </div>

          <div className="market-side-card">
            <div className="side-card-heading">
              <span>Top losers</span>
              <ArrowDownRight size={15} />
            </div>
            {losers.map((item) => (
              <MiniMover key={item.instrument.instrument_id} item={item} />
            ))}
          </div>

          <div className="market-side-card news-card">
            <div className="side-card-heading">
              <span>Financial news</span>
              <Newspaper size={15} />
            </div>

            {newsLoading ? (
              <div className="news-loading">Fetching market headlines…</div>
            ) : news.length ? (
              news.map((item, index) => (
                <a
                  key={`${item.title}-${index}`}
                  className="news-item"
                  href={item.link || "#"}
                  target="_blank"
                  rel="noreferrer"
                >
                  <div>
                    <strong>{item.title}</strong>
                    <span>{item.publisher || "Financial news"} · {item.published_at || "Latest"}</span>
                  </div>
                  <ExternalLink size={13} />
                </a>
              ))
            ) : (
              <div className="news-loading">No news available right now.</div>
            )}
          </div>
        </aside>
      </div>
    </section>
  );
}
