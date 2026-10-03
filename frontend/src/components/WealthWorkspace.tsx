import { useEffect, useMemo, useState } from "react";
import {
  BriefcaseBusiness,
  Heart,
  Plus,
  RefreshCw,
  Star,
  Trash2,
  Wallet,
} from "lucide-react";
import {
  getMarketQuote,
  type MarketQuote,
} from "../api/market";
import "./WealthWorkspace.css";

const supportedSymbols = [
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
];

type Holding = {
  id: string;
  symbol: string;
  quantity: number;
  averageCost: number;
};

type QuoteMap = Record<string, MarketQuote>;

function readStorage<T>(key: string, fallback: T): T {
  try {
    const value = window.localStorage.getItem(key);
    return value ? (JSON.parse(value) as T) : fallback;
  } catch {
    return fallback;
  }
}

function formatINR(value: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(value);
}

function formatPercent(value: number) {
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
}

export function WealthWorkspace() {
  const [tab, setTab] = useState<"watchlist" | "portfolio">("watchlist");
  const [watchlist, setWatchlist] = useState<string[]>(() =>
    readStorage<string[]>("finai.watchlist", ["TCS", "INFY", "RELIANCE"]),
  );
  const [holdings, setHoldings] = useState<Holding[]>(() =>
    readStorage<Holding[]>("finai.portfolio", []),
  );
  const [quotes, setQuotes] = useState<QuoteMap>({});
  const [newSymbol, setNewSymbol] = useState("TCS");
  const [newQuantity, setNewQuantity] = useState("10");
  const [newAverageCost, setNewAverageCost] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const portfolioSymbols = useMemo(
    () => Array.from(new Set(holdings.map((item) => item.symbol))),
    [holdings],
  );

  const trackedSymbols = useMemo(
    () => Array.from(new Set([...watchlist, ...portfolioSymbols])),
    [watchlist, portfolioSymbols],
  );

  const refreshQuotes = async () => {
    if (!trackedSymbols.length) return;

    setLoading(true);
    setError("");

    try {
      const entries = await Promise.all(
        trackedSymbols.map(async (symbol) => {
          const result = await getMarketQuote(symbol);
          return [symbol, result.quote] as const;
        }),
      );

      setQuotes(Object.fromEntries(entries));
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Unable to refresh tracked market prices.",
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    window.localStorage.setItem(
      "finai.watchlist",
      JSON.stringify(watchlist),
    );
    void refreshQuotes();
  }, [watchlist]);

  useEffect(() => {
    window.localStorage.setItem(
      "finai.portfolio",
      JSON.stringify(holdings),
    );
    void refreshQuotes();
  }, [holdings]);

  const addWatchlist = () => {
    const symbol = newSymbol.trim().toUpperCase();
    if (!symbol || watchlist.includes(symbol)) return;

    setWatchlist((current) => [...current, symbol]);
  };

  const removeWatchlist = (symbol: string) => {
    setWatchlist((current) => current.filter((item) => item !== symbol));
  };

  const addHolding = () => {
    const symbol = newSymbol.trim().toUpperCase();
    const quantity = Number(newQuantity);
    const averageCost = Number(newAverageCost);

    if (
      !symbol ||
      !Number.isFinite(quantity) ||
      quantity <= 0 ||
      !Number.isFinite(averageCost) ||
      averageCost <= 0
    ) {
      setError("Enter a valid symbol, quantity, and average cost.");
      return;
    }

    setError("");
    setHoldings((current) => [
      ...current,
      {
        id: `${symbol}-${Date.now()}`,
        symbol,
        quantity,
        averageCost,
      },
    ]);
    setNewAverageCost("");
  };

  const removeHolding = (id: string) => {
    setHoldings((current) => current.filter((item) => item.id !== id));
  };

  const portfolio = useMemo(() => {
    return holdings.map((holding) => {
      const currentPrice = Number(quotes[holding.symbol]?.price ?? 0);
      const invested = holding.quantity * holding.averageCost;
      const marketValue = holding.quantity * currentPrice;
      const pnl = marketValue - invested;
      const pnlPercent = invested ? (pnl / invested) * 100 : 0;

      return {
        ...holding,
        currentPrice,
        invested,
        marketValue,
        pnl,
        pnlPercent,
      };
    });
  }, [holdings, quotes]);

  const investedTotal = portfolio.reduce(
    (total, item) => total + item.invested,
    0,
  );
  const marketTotal = portfolio.reduce(
    (total, item) => total + item.marketValue,
    0,
  );
  const pnlTotal = marketTotal - investedTotal;
  const pnlPercent = investedTotal
    ? (pnlTotal / investedTotal) * 100
    : 0;

  return (
    <section className="wealth-workspace">
      <div className="wealth-header">
        <div>
          <div className="wealth-kicker">
            <Wallet size={14} />
            Wealth workspace
          </div>
          <h2>Track the positions that matter</h2>
          <p>
            Watchlist and portfolio views persist locally in this browser and
            use FinAI market quotes for current valuations.
          </p>
        </div>

        <button
          type="button"
          className="wealth-refresh"
          onClick={() => void refreshQuotes()}
          disabled={loading}
        >
          <RefreshCw size={14} />
          Refresh
        </button>
      </div>

      <div className="wealth-tabs">
        <button
          type="button"
          className={tab === "watchlist" ? "active" : ""}
          onClick={() => setTab("watchlist")}
        >
          <Star size={14} />
          Watchlist
        </button>
        <button
          type="button"
          className={tab === "portfolio" ? "active" : ""}
          onClick={() => setTab("portfolio")}
        >
          <BriefcaseBusiness size={14} />
          Portfolio
        </button>
      </div>

      {error && <div className="wealth-error">{error}</div>}

      {tab === "watchlist" ? (
        <div className="wealth-panel">
          <div className="wealth-add-row">
            <select
              value={newSymbol}
              onChange={(event) => setNewSymbol(event.target.value)}
            >
              {supportedSymbols.map((symbol) => (
                <option key={symbol}>{symbol}</option>
              ))}
            </select>
            <button type="button" onClick={addWatchlist}>
              <Plus size={14} />
              Add to watchlist
            </button>
          </div>

          <div className="watch-grid">
            {watchlist.map((symbol) => {
              const quote = quotes[symbol];
              const current = Number(quote?.price ?? 0);
              const open = Number(quote?.open ?? 0);
              const changePercent =
                open > 0 ? ((current - open) / open) * 100 : 0;

              return (
                <article className="watch-card" key={symbol}>
                  <div className="watch-card-top">
                    <div>
                      <span className="watch-symbol">{symbol}</span>
                      <span className="watch-source">
                        {quote?.source ?? "Awaiting market data"}
                      </span>
                    </div>
                    <button
                      type="button"
                      className="icon-danger"
                      onClick={() => removeWatchlist(symbol)}
                      aria-label={`Remove ${symbol}`}
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>

                  <strong>{current ? formatINR(current) : "—"}</strong>

                  <div
                    className={
                      changePercent >= 0
                        ? "watch-change positive"
                        : "watch-change negative"
                    }
                  >
                    {formatPercent(changePercent)}
                  </div>
                </article>
              );
            })}

            {!watchlist.length && (
              <div className="wealth-empty">
                <Heart size={18} />
                Add instruments to build your watchlist.
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="wealth-panel">
          <div className="portfolio-summary">
            <div>
              <span>Invested</span>
              <strong>{formatINR(investedTotal)}</strong>
            </div>
            <div>
              <span>Market value</span>
              <strong>{formatINR(marketTotal)}</strong>
            </div>
            <div>
              <span>Total P&amp;L</span>
              <strong className={pnlTotal >= 0 ? "positive" : "negative"}>
                {formatINR(pnlTotal)}
              </strong>
            </div>
            <div>
              <span>Return</span>
              <strong className={pnlPercent >= 0 ? "positive" : "negative"}>
                {formatPercent(pnlPercent)}
              </strong>
            </div>
          </div>

          <div className="wealth-add-row portfolio-form">
            <select
              value={newSymbol}
              onChange={(event) => setNewSymbol(event.target.value)}
            >
              {supportedSymbols.map((symbol) => (
                <option key={symbol}>{symbol}</option>
              ))}
            </select>
            <input
              type="number"
              min="0.01"
              step="0.01"
              value={newQuantity}
              onChange={(event) => setNewQuantity(event.target.value)}
              placeholder="Qty"
            />
            <input
              type="number"
              min="0.01"
              step="0.01"
              value={newAverageCost}
              onChange={(event) => setNewAverageCost(event.target.value)}
              placeholder="Avg cost"
            />
            <button type="button" onClick={addHolding}>
              <Plus size={14} />
              Add holding
            </button>
          </div>

          <div className="portfolio-table-wrap">
            {portfolio.length ? (
              <table className="portfolio-table">
                <thead>
                  <tr>
                    <th>Instrument</th>
                    <th>Qty</th>
                    <th>Avg cost</th>
                    <th>Price</th>
                    <th>Market value</th>
                    <th>P&amp;L</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {portfolio.map((item) => (
                    <tr key={item.id}>
                      <td>
                        <strong>{item.symbol}</strong>
                        <span>Live market quote</span>
                      </td>
                      <td>{item.quantity}</td>
                      <td>{formatINR(item.averageCost)}</td>
                      <td>{formatINR(item.currentPrice)}</td>
                      <td>{formatINR(item.marketValue)}</td>
                      <td className={item.pnl >= 0 ? "positive" : "negative"}>
                        <strong>{formatINR(item.pnl)}</strong>
                        <span>{formatPercent(item.pnlPercent)}</span>
                      </td>
                      <td>
                        <button
                          type="button"
                          className="icon-danger"
                          onClick={() => removeHolding(item.id)}
                          aria-label={`Remove ${item.symbol}`}
                        >
                          <Trash2 size={14} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="wealth-empty">
                <BriefcaseBusiness size={18} />
                Your portfolio is empty. Add a holding above to calculate live
                market value and P&amp;L.
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
}

export default WealthWorkspace;
