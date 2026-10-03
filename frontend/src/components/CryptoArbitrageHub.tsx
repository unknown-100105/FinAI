import { useEffect, useMemo, useState } from "react";
import { ArrowRightLeft, Calculator, RefreshCw, Search, ShieldCheck, TriangleAlert } from "lucide-react";
import {
  estimateCryptoArbitrage,
  getCryptoConnectors,
  getCryptoTickers,
  scanAllCryptoPairs,
  type ArbitrageEstimateRequest,
} from "../api/crypto";
import { getMarketHistory, getMarketQuote, type MarketBar, type MarketQuote } from "../api/market";
import "./PlatformModules.css";

function usd(value: unknown) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "—";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 2 }).format(number);
}

function number(value: unknown, digits = 4) {
  const n = Number(value);
  return Number.isFinite(n) ? n.toFixed(digits) : "—";
}

type Opportunity = Record<string, any>;

const chartRanges = [
  { id: "1D", days: 1, interval: "15m" },
  { id: "7D", days: 7, interval: "1h" },
  { id: "30D", days: 30, interval: "1h" },
  { id: "90D", days: 90, interval: "1d" },
];

export function CryptoArbitrageHub() {
  const [asset, setAsset] = useState("BTC/USDT");
  const [buyVenue, setBuyVenue] = useState("binance");
  const [sellVenue, setSellVenue] = useState("bybit");
  const [capital, setCapital] = useState("1000");
  const [buyPrice, setBuyPrice] = useState("100000");
  const [sellPrice, setSellPrice] = useState("101000");
  const [buyFee, setBuyFee] = useState("0.1");
  const [sellFee, setSellFee] = useState("0.1");
  const [slippage, setSlippage] = useState("0.05");
  const [transfer, setTransfer] = useState("2");
  const [tax, setTax] = useState("0");
  const [estimate, setEstimate] = useState<any | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const [connectors, setConnectors] = useState<any[]>([]);
  const [registeredServices, setRegisteredServices] = useState<any[]>([]);
  const [selectedExchanges, setSelectedExchanges] = useState<string[]>(["binance", "bybit", "kucoin", "coinbase"]);
  const [scan, setScan] = useState<any | null>(null);
  const [tickerExchange, setTickerExchange] = useState("binance");
  const [tickerQuote, setTickerQuote] = useState("USDT");
  const [tickerSearch, setTickerSearch] = useState("");
  const [tickers, setTickers] = useState<any[]>([]);
  const [tickerCount, setTickerCount] = useState(0);
  const [tickersBusy, setTickersBusy] = useState(false);
  const [miningHashrate, setMiningHashrate] = useState("200");
  const [miningPower, setMiningPower] = useState("3500");
  const [miningElectricity, setMiningElectricity] = useState("0.10");
  const [miningData, setMiningData] = useState<any | null>(null);
  const [miningBusy, setMiningBusy] = useState(false);

  const [chartSymbol, setChartSymbol] = useState("BTC");
  const [chartRange, setChartRange] = useState("1D");
  const [chartBars, setChartBars] = useState<MarketBar[]>([]);
  const [chartQuote, setChartQuote] = useState<MarketQuote | null>(null);
  const [chartError, setChartError] = useState("");

  const chartConfig = chartRanges.find((item) => item.id === chartRange) ?? chartRanges[0];
  const chartPoints = useMemo(() => {
    if (chartBars.length < 2) return "";
    const values = chartBars.map((bar) => bar.close);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const spread = max - min || 1;
    return chartBars.map((bar, index) => {
      const x = (index / Math.max(1, chartBars.length - 1)) * 720;
      const y = 15 + (1 - (bar.close - min) / spread) * 220;
      return x.toFixed(1) + "," + y.toFixed(1);
    }).join(" ");
  }, [chartBars]);

  const loadChart = async () => {
    setChartError("");
    const end = new Date();
    const start = new Date();
    start.setDate(end.getDate() - chartConfig.days);
    try {
      const [quote, history] = await Promise.all([
        getMarketQuote(chartSymbol),
        getMarketHistory(chartSymbol, start.toISOString(), end.toISOString(), chartConfig.interval),
      ]);
      setChartQuote(quote.quote);
      setChartBars(history.bars);
    } catch (requestError) {
      setChartQuote(null);
      setChartBars([]);
      setChartError(requestError instanceof Error ? requestError.message : "Crypto chart unavailable.");
    }
  };

  useEffect(() => { void loadChart(); }, [chartSymbol, chartRange]);
  useEffect(() => {
    const timer = window.setInterval(() => { void loadChart(); }, 10000);
    return () => window.clearInterval(timer);
  }, [chartSymbol, chartRange]);
  useEffect(() => {
    const timer = window.setInterval(() => { void loadTickers(); }, 15000);
    return () => window.clearInterval(timer);
  }, [tickerExchange, tickerSearch]);

  useEffect(() => {
    void getCryptoConnectors().then((data) => {
      setConnectors(data.connectors || []);
      setRegisteredServices(data.registered_vda_services || []);
    }).catch(() => setConnectors([]));
  }, []);

  const loadTickers = async () => {
    setTickersBusy(true);
    try {
      const result = await getCryptoTickers(tickerExchange, tickerQuote, tickerSearch, 500, 0);
      setTickers(result.tickers || []);
      setTickerCount(Number(result.count || 0));
    } catch {
      setTickers([]);
      setTickerCount(0);
    } finally {
      setTickersBusy(false);
    }
  };

  useEffect(() => { void loadTickers(); }, [tickerExchange, tickerQuote]);

  const runEstimate = async () => {
    setLoading(true);
    setError("");
    const request: ArbitrageEstimateRequest = {
      asset, buy_venue: buyVenue, sell_venue: sellVenue,
      capital_quote: Number(capital), buy_price: Number(buyPrice), sell_price: Number(sellPrice),
      buy_fee_percent: Number(buyFee), sell_fee_percent: Number(sellFee),
      buy_slippage_percent: Number(slippage), sell_slippage_percent: Number(slippage),
      transfer_cost_quote: Number(transfer), tax_rate_percent: Number(tax),
    };
    try {
      setEstimate(await estimateCryptoArbitrage(request));
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to estimate arbitrage.");
    } finally {
      setLoading(false);
    }
  };

  const runAllPairs = async () => {
    setLoading(true);
    setError("");
    try {
      const result = await scanAllCryptoPairs({
        exchanges: selectedExchanges,
        quote: "USDT",
        capital_quote: Number(capital),
        buy_fee_percent: Number(buyFee),
        sell_fee_percent: Number(sellFee),
        buy_slippage_percent: Number(slippage),
        sell_slippage_percent: Number(slippage),
        transfer_cost_quote: Number(transfer),
        tax_rate_percent: Number(tax),
        top_n: 50,
      });
      setScan(result);
      const top = result.opportunities?.[0];
      if (top) {
        setAsset(top.asset);
        setBuyVenue(top.buy_venue);
        setSellVenue(top.sell_venue);
        setBuyPrice(String(top.buy_price));
        setSellPrice(String(top.sell_price));
        setChartSymbol(String(top.asset).split("/")[0]);
      }
    } catch (requestError) {
      setScan(null);
      setError(requestError instanceof Error ? requestError.message : "All-pair scan unavailable.");
    } finally {
      setLoading(false);
    }
  };

  const toggleExchange = (exchange: string) => {
    setSelectedExchanges((current) =>
      current.includes(exchange)
        ? current.filter((item) => item !== exchange)
        : [...current, exchange],
    );
  };

  return (
    <section className="module-page">
      <div className="module-hero">
        <div>
          <div className="module-kicker"><ArrowRightLeft size={14} /> Cross-venue crypto intelligence</div>
          <h1>Discover the market before calculating the spread.</h1>
          <p>Dynamic pair discovery, live public tickers, cross-venue opportunity scanning and chart-backed investigation. Regulatory status is shown as a reporting-entity reference, not government endorsement.</p>
        </div>
        <div className="module-orb"><Calculator size={23} /></div>
      </div>

      <section className="workspace-panel">
        <div className="module-panel-head">
          <div><div className="module-kicker">Regulatory / connectivity universe</div><h2>FIU-IND reporting-entity snapshot + public connectors</h2></div>
          <a className="source-link" href="https://sansad.in/getFile/loksabhaquestions/annex/187/AU5805_lMTYNK.pdf?source=pqals" target="_blank" rel="noreferrer">Official snapshot ↗</a>
        </div>
        <div className="connector-grid">
          {connectors.map((item: any) => (
            <button key={item.exchange_id} type="button" className={selectedExchanges.includes(item.exchange_id) ? "connector-card active" : "connector-card"} onClick={() => toggleExchange(item.exchange_id)}>
              <strong>{item.trade_name}</strong>
              <span>{item.exchange_id} · FIU snapshot 09-03-2026</span>
            </button>
          ))}
        </div>
        <p className="data-note">The Government's 30-03-2026 Lok Sabha answer says 54 VDA service providers were registered with FIU-IND as of 09-03-2026, while also warning that the register is not a public licence/endorsement list. FinAI therefore separates regulatory status from actual market connectivity.</p>
        <details className="registry-details">
          <summary>View 54-provider FIU-IND reporting-entity snapshot</summary>
          <div className="registry-table-wrap">
            <table className="ticker-table"><thead><tr><th>Trade name</th><th>Registered entity</th><th>Country</th><th>Status</th></tr></thead>
              <tbody>{registeredServices.map((item: any, index: number) => <tr key={item.trade_name + item.registered_entity + index}><td><strong>{item.trade_name}</strong></td><td>{item.registered_entity}</td><td>{item.country}</td><td>{item.status}</td></tr>)}</tbody>
            </table>
          </div>
        </details>
      </section>

      <section className="workspace-panel crypto-universe-panel">
        <div className="module-panel-head">
          <div><div className="module-kicker">All-pair market universe</div><h2>{tickerExchange.toUpperCase()} · {tickerCount.toLocaleString()} {tickerQuote} pairs with public ticker snapshots</h2></div>
          <button className="market-refresh" type="button" onClick={() => void loadTickers()} disabled={tickersBusy}><RefreshCw size={13}/> Refresh</button>
        </div>
        <div className="crypto-universe-toolbar">
          <div className="crypto-selector-row">
            <select value={tickerExchange} onChange={(e) => setTickerExchange(e.target.value)}>
              {connectors.map((item: any) => <option key={item.exchange_id} value={item.exchange_id}>{item.trade_name}</option>)}
            </select>
            <select value={tickerQuote} onChange={(e) => setTickerQuote(e.target.value)}>
              {["USDT","USDC","INR","BTC","ETH"].map((value) => <option key={value} value={value}>{value}</option>)}
            </select>
          </div>
          <div className="compliance-search"><Search size={13}/><input value={tickerSearch} onChange={(e) => setTickerSearch(e.target.value)} placeholder="Filter pairs, e.g. BTC, ETH, SOL" /><button type="button" onClick={() => void loadTickers()}>Search</button></div>
        </div>
        <div className="ticker-table-wrap">
          <table className="ticker-table"><thead><tr><th>Pair</th><th>Last</th><th>Bid</th><th>Ask</th><th>Spread</th><th>24h Quote Volume</th></tr></thead>
            <tbody>{tickers.map((item: any) => {
              const spread = Number(item.ask) > 0 && Number(item.bid) > 0 ? (Number(item.ask) - Number(item.bid)) / Number(item.bid) * 100 : null;
              return <tr key={item.symbol} onClick={() => { setAsset(item.symbol); setChartSymbol(item.symbol.split("/")[0]); }}><td><strong>{item.symbol}</strong></td><td>{number(item.last, 8)}</td><td>{number(item.bid, 8)}</td><td>{number(item.ask, 8)}</td><td>{spread == null ? "—" : spread.toFixed(3) + "%"}</td><td>{Number(item.quote_volume).toLocaleString(undefined, { maximumFractionDigits: 0 })}</td></tr>;
            })}</tbody>
          </table>
          {!tickers.length && <div className="module-empty">No live tickers returned for this exchange/filter.</div>}
        </div>
        <div className="data-note">The table is dynamic; it is not a hardcoded coin list. Public exchange APIs determine the currently available pair universe and may differ by jurisdiction/account.</div>
      </section>

      <section className="workspace-panel crypto-opportunity-panel">
        <div className="module-panel-head">
          <div><div className="module-kicker">Cross-market scanner</div><h2>Top estimated opportunities across selected connectors</h2></div>
          <span className="source-chip">Snapshot analysis</span>
        </div>
        <div className="arb-fields">
          <label>Capital<input type="number" value={capital} onChange={(e) => setCapital(e.target.value)} /></label>
          <label>Buy fee %<input type="number" value={buyFee} onChange={(e) => setBuyFee(e.target.value)} /></label>
          <label>Sell fee %<input type="number" value={sellFee} onChange={(e) => setSellFee(e.target.value)} /></label>
          <label>Buy slippage %<input type="number" value={slippage} onChange={(e) => setSlippage(e.target.value)} /></label>
          <label>Transfer cost<input type="number" value={transfer} onChange={(e) => setTransfer(e.target.value)} /></label>
          <label>Tax assumption %<input type="number" value={tax} onChange={(e) => setTax(e.target.value)} /></label>
        </div>
        <div className="arb-actions">
          <button type="button" onClick={() => void runAllPairs()} disabled={loading}><RefreshCw size={14}/> Scan all pairs</button>
          <button type="button" className="secondary-action" onClick={() => void runEstimate()} disabled={loading}><Calculator size={14}/> Calculate selected pair</button>
        </div>
        {scan && (
          <>
            <div className="scanner-summary">
              <div><span>Pairs across venue snapshots</span><strong>{Number(scan.pair_count).toLocaleString()}</strong></div>
              <div><span>Estimated opportunities</span><strong>{Number(scan.opportunity_count).toLocaleString()}</strong></div>
              <div><span>Venues scanned</span><strong>{scan.exchanges_scanned.join(", ") || "—"}</strong></div>
            </div>
            <div className="opportunity-table-wrap">
              <table className="ticker-table"><thead><tr><th>Pair</th><th>Buy</th><th>Sell</th><th>Buy ask</th><th>Sell bid</th><th>Net profit</th><th>Net return</th></tr></thead>
                <tbody>{(scan.opportunities || []).map((item: Opportunity, index: number) =>
                  <tr key={index} onClick={() => { setAsset(item.asset); setChartSymbol(item.asset.split("/")[0]); setBuyVenue(item.buy_venue); setSellVenue(item.sell_venue); }}>
                    <td><strong>{item.asset}</strong></td><td>{item.buy_venue}</td><td>{item.sell_venue}</td>
                    <td>{number(item.buy_price, 8)}</td><td>{number(item.sell_price, 8)}</td>
                    <td className={Number(item.net_profit_quote) > 0 ? "market-positive" : "market-negative"}>{usd(item.net_profit_quote)}</td>
                    <td>{number(item.net_return_percent, 3)}%</td>
                  </tr>,
                )}</tbody>
              </table>
            </div>
          </>
        )}
        {estimate && <div className="result-panel"><span>Selected-pair net estimate</span><strong>{usd(estimate.net_profit_quote)}</strong><small>Return {number(estimate.net_return_percent, 3)}% · breakeven {usd(estimate.break_even_sell_price)}</small></div>}
        <div className="arb-warning"><TriangleAlert size={14}/><span>Top rows are ranked by calculated snapshot return, not guaranteed profit. A trade can disappear because of depth, transfer time, withdrawal limits, account limits, taxes, fees, latency or venue availability.</span></div>
      </section>

      <section className="workspace-panel mining-panel">
        <div className="module-panel-head">
          <div><div className="module-kicker">Proof-of-work economics</div><h2>Live Bitcoin network + mining profitability model</h2></div>
          <span className="source-chip">Mempool network snapshot</span>
        </div>
        <div className="arb-fields">
          <label>Miner hash rate (TH/s)<input type="number" value={miningHashrate} onChange={(e) => setMiningHashrate(e.target.value)} /></label>
          <label>Power (watts)<input type="number" value={miningPower} onChange={(e) => setMiningPower(e.target.value)} /></label>
          <label>Electricity (USD/kWh)<input type="number" value={miningElectricity} onChange={(e) => setMiningElectricity(e.target.value)} /></label>
        </div>
        <button className="primary-module-button" type="button" disabled={miningBusy} onClick={() => {
          setMiningBusy(true);
          void getBitcoinMiningSnapshot({
            hashrate_ths: Number(miningHashrate),
            power_watts: Number(miningPower),
            electricity_usd_kwh: Number(miningElectricity),
          }).then(setMiningData).catch((requestError) => setError(requestError instanceof Error ? requestError.message : "Live mining data unavailable."))
            .finally(() => setMiningBusy(false));
        }}>{miningBusy ? "Reading network…" : "Refresh mining economics"}</button>
        {miningData && <div className="mining-results">
          <div><span>Network hashrate</span><strong>{number(miningData.network_hashrate_eh_s, 2)} EH/s</strong></div>
          <div><span>Difficulty</span><strong>{Number(miningData.difficulty || 0).toLocaleString()}</strong></div>
          <div><span>BTC price</span><strong>{usd(miningData.btc_price_usd)}</strong></div>
          <div><span>Expected BTC/day</span><strong>{number(miningData.economics.expected_btc_per_day, 8)}</strong></div>
          <div><span>Gross/day</span><strong>{usd(miningData.economics.gross_revenue_usd_per_day)}</strong></div>
          <div><span>Electricity/day</span><strong>{usd(miningData.economics.electricity_cost_usd_per_day)}</strong></div>
          <div><span>Net before pool/hardware/tax</span><strong className={Number(miningData.economics.net_before_pool_hardware_tax_usd_per_day) >= 0 ? "market-positive" : "market-negative"}>{usd(miningData.economics.net_before_pool_hardware_tax_usd_per_day)}</strong></div>
          <div><span>Break-even electricity</span><strong>{usd(miningData.economics.break_even_electricity_usd_kwh)}</strong></div>
        </div>}
        <div className="data-note">Live network hashrate, difficulty, block-reward and pool statistics are sourced from Mempool. This calculation is probabilistic and excludes hardware depreciation, maintenance, pool fee and taxes from the displayed net unless you model them separately.</div>
      </section>

      <section className="workspace-panel crypto-chart-panel">
        <div className="module-panel-head">
          <div><div className="module-kicker">Investigate the selected opportunity</div><h2>{chartSymbol}/USDT live-history chart</h2></div>
          <span className="source-chip">{chartQuote?.source || "market feed"}</span>
        </div>
        <div className="crypto-chart-toolbar">
          <div className="market-quick-list">{["BTC","ETH","SOL","XRP","DOGE","ADA","AVAX"].map((symbol) => <button key={symbol} type="button" className={chartSymbol === symbol ? "active" : ""} onClick={() => setChartSymbol(symbol)}>{symbol}</button>)}</div>
          <div className="range-tabs">{chartRanges.map((item) => <button key={item.id} type="button" className={chartRange === item.id ? "active" : ""} onClick={() => setChartRange(item.id)}>{item.id}</button>)}</div>
        </div>
        {chartError && <div className="module-error">{chartError}</div>}
        <div className="crypto-chart-meta"><span>Last {chartQuote?.price ? usd(chartQuote.price) : "—"}</span><span>{chartQuote?.timestamp ? new Date(chartQuote.timestamp).toLocaleString() : "latest available"}</span></div>
        <div className="crypto-chart-wrap">{chartBars.length > 1 ? <svg viewBox="0 0 720 250" preserveAspectRatio="none" role="img" aria-label={chartSymbol + " crypto chart"}><polyline points={chartPoints} fill="none" stroke="currentColor" strokeWidth="3" vectorEffect="non-scaling-stroke" className="chart-line-positive" /></svg> : <div className="module-empty">No chart bars returned.</div>}</div>
      </section>
    </section>
  );
}

export default CryptoArbitrageHub;
