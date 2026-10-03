import { useEffect, useMemo, useState } from "react";
import { ArrowRightLeft, Calculator, RefreshCw, ShieldCheck, TriangleAlert } from "lucide-react";
import { estimateCryptoArbitrage, scanCryptoArbitrage } from "../api/crypto";
import { getMarketHistory, getMarketQuote, type MarketBar, type MarketQuote } from "../api/market";
import "./PlatformModules.css";

function money(value: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(value);
}

export function CryptoArbitrageHub() {
  const [asset, setAsset] = useState("BTC/USDT");
  const [buyVenue, setBuyVenue] = useState("venue-a");
  const [sellVenue, setSellVenue] = useState("venue-b");
  const [capital, setCapital] = useState("1000");
  const [buyPrice, setBuyPrice] = useState("100000");
  const [sellPrice, setSellPrice] = useState("101000");
  const [buyFee, setBuyFee] = useState("0.1");
  const [sellFee, setSellFee] = useState("0.1");
  const [slippage, setSlippage] = useState("0.05");
  const [transfer, setTransfer] = useState("2");
  const [tax, setTax] = useState("0");
  const [estimate, setEstimate] = useState<any | null>(null);
  const [scan, setScan] = useState<any | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [chartSymbol, setChartSymbol] = useState("BTC");
  const [chartRange, setChartRange] = useState("1D");
  const [chartInterval, setChartInterval] = useState("15m");
  const [chartBars, setChartBars] = useState<MarketBar[]>([]);
  const [chartQuote, setChartQuote] = useState<MarketQuote | null>(null);
  const [chartError, setChartError] = useState("");
  const chartRanges = [{ id: "1D", days: 1 }, { id: "7D", days: 7 }, { id: "30D", days: 30 }, { id: "90D", days: 90 }];
  const chartPoints = useMemo(() => {
    if (chartBars.length < 2) return "";
    const closes = chartBars.map((bar) => bar.close);
    const min = Math.min(...closes);
    const max = Math.max(...closes);
    const spread = max - min || 1;
    return chartBars.map((bar, index) => {
      const x = (index / Math.max(1, chartBars.length - 1)) * 720;
      const y = 250 - ((bar.close - min) / spread) * 220;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(" ");
  }, [chartBars]);

  const loadCryptoChart = async () => {
    setChartError("");
    const days = chartRanges.find((item) => item.id === chartRange)?.days ?? 1;
    const end = new Date();
    const start = new Date();
    start.setDate(end.getDate() - days);
    try {
      const [quote, history] = await Promise.all([
        getMarketQuote(chartSymbol),
        getMarketHistory(chartSymbol, start.toISOString(), end.toISOString(), chartInterval),
      ]);
      setChartQuote(quote.quote);
      setChartBars(history.bars);
    } catch (requestError) {
      setChartBars([]);
      setChartQuote(null);
      setChartError(requestError instanceof Error ? requestError.message : "Crypto chart unavailable.");
    }
  };

  useEffect(() => { void loadCryptoChart(); }, [chartSymbol, chartRange, chartInterval]);

  const runEstimate = async () => {
    setLoading(true);
    setError("");
    try {
      const result = await estimateCryptoArbitrage({
        asset,
        buy_venue: buyVenue,
        sell_venue: sellVenue,
        capital_quote: Number(capital),
        buy_price: Number(buyPrice),
        sell_price: Number(sellPrice),
        buy_fee_percent: Number(buyFee),
        sell_fee_percent: Number(sellFee),
        buy_slippage_percent: Number(slippage),
        sell_slippage_percent: Number(slippage),
        transfer_cost_quote: Number(transfer),
        tax_rate_percent: Number(tax),
      });
      setEstimate(result);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to estimate arbitrage.");
    } finally {
      setLoading(false);
    }
  };

  const runScan = async () => {
    setLoading(true);
    setError("");
    try {
      const result = await scanCryptoArbitrage({
        symbol: asset,
        exchanges: ["binance", "bybit", "okx", "kucoin"],
        capital_quote: Number(capital),
        buy_fee_percent: Number(buyFee),
        sell_fee_percent: Number(sellFee),
        buy_slippage_percent: Number(slippage),
        sell_slippage_percent: Number(slippage),
        transfer_cost_quote: Number(transfer),
        tax_rate_percent: Number(tax),
      });
      setScan(result);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Live exchange scan is unavailable.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="module-page">
      <div className="module-hero">
        <div>
          <div className="module-kicker"><ArrowRightLeft size={14} /> Cross-venue crypto research</div>
          <h1>Compare venues before believing the spread.</h1>
          <p>FinAI estimates theoretical cross-exchange profit after fees, slippage and transfer costs. It does not place trades.</p>
        </div>
        <div className="module-orb"><Calculator size={23} /></div>
      </div>

      <section className="workspace-panel crypto-chart-panel">
        <div className="module-panel-head">
          <div><div className="module-kicker">Crypto market feed</div><h2>{chartSymbol}/USD chart</h2></div>
          <span className="source-chip">Provider snapshot</span>
        </div>
        <div className="crypto-chart-toolbar">
          <div className="market-quick-list">{["BTC","ETH","SOL","DOGE"].map((symbol) => <button key={symbol} type="button" className={chartSymbol === symbol ? "active" : ""} onClick={() => setChartSymbol(symbol)}>{symbol}</button>)}</div>
          <div className="range-tabs">{chartRanges.map((item) => <button key={item.id} type="button" className={chartRange === item.id ? "active" : ""} onClick={() => setChartRange(item.id)}>{item.id}</button>)}</div>
          <div className="range-tabs">{["1m","5m","15m","1h","1d"].map((value) => <button key={value} type="button" className={chartInterval === value ? "active" : ""} disabled={chartRange === "90D" && ["1m","5m","15m","1h"].includes(value)} onClick={() => setChartInterval(value)}>{value}</button>)}</div>
        </div>
        {chartError && <div className="module-error">{chartError}</div>}
        <div className="crypto-chart-meta">
          <span>Last {chartQuote?.price ? money(Number(chartQuote.price)) : "—"}</span>
          <span>{chartQuote?.timestamp ? new Date(chartQuote.timestamp).toLocaleString() : "latest available"}</span>
        </div>
        <div className="crypto-chart-wrap">
          {chartBars.length > 1 ? <svg viewBox="0 0 720 270" preserveAspectRatio="none" role="img" aria-label={`${chartSymbol} crypto price chart`}><polyline points={chartPoints} fill="none" stroke="currentColor" strokeWidth="3" vectorEffect="non-scaling-stroke" className="chart-line-positive" /></svg> : <div className="module-empty">{loading ? "Loading crypto market feed…" : "No crypto bars returned."}</div>}
        </div>
      </section>

      <div className="arb-layout">
        <section className="arb-panel">
          <div className="module-panel-head">
            <div><div className="module-kicker">Scenario</div><h2>Arbitrage estimator</h2></div>
            <ShieldCheck size={17} />
          </div>

          <div className="arb-fields">
            {[
              ["Asset", asset, setAsset],
              ["Buy venue", buyVenue, setBuyVenue],
              ["Sell venue", sellVenue, setSellVenue],
              ["Capital (quote)", capital, setCapital],
              ["Buy price", buyPrice, setBuyPrice],
              ["Sell price", sellPrice, setSellPrice],
              ["Buy fee %", buyFee, setBuyFee],
              ["Sell fee %", sellFee, setSellFee],
              ["Slippage %", slippage, setSlippage],
              ["Transfer cost", transfer, setTransfer],
              ["Tax assumption %", tax, setTax],
            ].map(([label, value, setter]) => (
              <label key={label as string}>
                {label as string}
                <input
                  value={value as string}
                  onChange={(event) => (setter as (value: string) => void)(event.target.value)}
                  type={["Asset", "Buy venue", "Sell venue"].includes(label as string) ? "text" : "number"}
                />
              </label>
            ))}
          </div>

          <div className="arb-actions">
            <button type="button" onClick={() => void runEstimate()} disabled={loading}>
              <Calculator size={14} /> {loading ? "Calculating…" : "Estimate profit"}
            </button>
            <button type="button" onClick={() => void runScan()} disabled={loading} className="secondary-action">
              <RefreshCw size={14} /> Scan public venues
            </button>
          </div>

          <div className="arb-warning"><TriangleAlert size={14} /><span>Snapshots can become stale before a trade executes. Order-book depth, withdrawal limits, settlement time, taxes and execution failures can erase an apparent opportunity.</span></div>
          {error && <div className="module-error">{error}</div>}
        </section>

        <aside className="arb-results">
          <div className="calc-result-card">
            <span>Estimated net profit</span>
            <strong>{estimate ? money(Number(estimate.net_profit_quote)) : "—"}</strong>
            <small>{estimate ? `${Number(estimate.net_return_percent).toFixed(2)}% of capital` : "Run a scenario to calculate."}</small>
          </div>

          {estimate && (
            <div className="arb-metrics">
              <div><span>Quantity</span><strong>{Number(estimate.quantity).toFixed(6)}</strong></div>
              <div><span>Break-even sell</span><strong>{money(Number(estimate.break_even_sell_price))}</strong></div>
              <div><span>Fees</span><strong>{money(Number(estimate.buy_fee_quote + estimate.sell_fee_quote))}</strong></div>
              <div><span>Transfer</span><strong>{money(Number(estimate.transfer_cost_quote))}</strong></div>
            </div>
          )}

          {scan && (
            <div className="scan-card">
              <div className="side-title"><ArrowRightLeft size={14} /> Public venue scan</div>
              {scan.opportunities.slice(0, 6).map((item: any, index: number) => (
                <div className="scan-row" key={index}>
                  <div><strong>{item.buy_venue} → {item.sell_venue}</strong><span>{item.buy_price} → {item.sell_price}</span></div>
                  <strong className={Number(item.net_profit_quote) >= 0 ? "positive" : "negative"}>{money(Number(item.net_profit_quote))}</strong>
                </div>
              ))}
              {!scan.opportunities.length && <div className="module-empty">No two-sided opportunities returned.</div>}
            </div>
          )}
        </aside>
      </div>
    </section>
  );
}

export default CryptoArbitrageHub;
