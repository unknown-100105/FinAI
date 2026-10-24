import { useMemo, useState } from "react";
import { Activity, FlaskConical } from "lucide-react";
import type { MarketBar } from "../api/market";

type BacktestTrade = {
  entryTime: string;
  exitTime: string;
  entryPrice: number;
  exitPrice: number;
  returnPct: number;
  holdingBars: number;
};

type BacktestResult = {
  error?: string;
  initialCapital: number;
  finalEquity: number;
  netReturnPct: number;
  buyHoldReturnPct: number;
  maxDrawdownPct: number;
  closedTrades: number;
  wins: number;
  winRatePct: number | null;
  profitFactor: number | null;
  trades: BacktestTrade[];
  equityCurve: number[];
  dataBars: number;
  shortWindow: number;
  longWindow: number;
  feeBps: number;
  slippageBps: number;
};

function movingAverage(values: number[], period: number): Array<number | null> {
  const result: Array<number | null> = Array(values.length).fill(null);
  let rollingSum = 0;
  for (let index = 0; index < values.length; index += 1) {
    rollingSum += values[index];
    if (index >= period) rollingSum -= values[index - period];
    if (index >= period - 1) result[index] = rollingSum / period;
  }
  return result;
}

function runSmaCrossover(
  bars: MarketBar[],
  shortWindow: number,
  longWindow: number,
  initialCapital: number,
  feeBps: number,
  slippageBps: number,
): BacktestResult {
  const empty: BacktestResult = {
    initialCapital, finalEquity: initialCapital, netReturnPct: 0,
    buyHoldReturnPct: 0, maxDrawdownPct: 0, closedTrades: 0,
    wins: 0, winRatePct: null, profitFactor: null, trades: [], equityCurve: [initialCapital],
    dataBars: bars.length, shortWindow, longWindow, feeBps, slippageBps,
  };
  if (!Number.isInteger(shortWindow) || shortWindow < 2) {
    return { ...empty, error: "Short SMA must be a whole number of at least 2 bars." };
  }
  if (!Number.isInteger(longWindow) || longWindow <= shortWindow) {
    return { ...empty, error: "Long SMA must be a whole number greater than short SMA." };
  }
  if (!Number.isFinite(initialCapital) || initialCapital <= 0) {
    return { ...empty, error: "Starting capital must be positive." };
  }
  if (!Number.isFinite(feeBps) || feeBps < 0 || !Number.isFinite(slippageBps) || slippageBps < 0) {
    return { ...empty, error: "Fees and slippage must be non-negative basis-point values." };
  }
  if (feeBps + slippageBps >= 5000) {
    return { ...empty, error: "Combined fee and slippage assumption must be below 5,000 bps." };
  }
  if (bars.length <= longWindow) {
    return { ...empty, error: `Need at least ${longWindow + 1} bars for this configuration.` };
  }
  const valid = bars.every((bar) =>
    typeof bar.timestamp === "string"
    && Number.isFinite(Number(bar.open))
    && Number.isFinite(Number(bar.close))
    && Number(bar.open) > 0
    && Number(bar.close) > 0
  );
  if (!valid) {
    return { ...empty, error: "History contains missing or invalid open/close prices. Refresh data before testing." };
  }

  const closes = bars.map((bar) => Number(bar.close));
  const shortMeans = movingAverage(closes, shortWindow);
  const longMeans = movingAverage(closes, longWindow);
  const costRate = (feeBps + slippageBps) / 10_000;
  const startIndex = longWindow;
  const startOpen = Number(bars[startIndex].open);
  const lastClose = Number(bars[bars.length - 1].close);
  const buyHoldFinal = initialCapital * (lastClose * (1 - costRate)) / (startOpen * (1 + costRate));
  let cash = initialCapital;
  let quantity = 0;
  let inPosition = false;
  let entryTime = "";
  let entryPrice = 0;
  let entryEquity = 0;
  let entryIndex = 0;
  let peakEquity = initialCapital;
  let maxDrawdown = 0;
  let positivePnl = 0;
  let negativePnl = 0;
  const trades: BacktestTrade[] = [];
  const equityCurve: number[] = [initialCapital];

  for (let index = startIndex; index < bars.length; index += 1) {
    // Only use the crossover known at the previous bar close, then execute
    // at the current bar open. This avoids executing on the signal candle.
    const signalIndex = index - 1;
    const shortValue = shortMeans[signalIndex];
    const longValue = longMeans[signalIndex];
    const desiredLong = shortValue !== null && longValue !== null && shortValue > longValue;
    const open = Number(bars[index].open);

    if (desiredLong && !inPosition) {
      entryPrice = open * (1 + costRate);
      entryEquity = cash;
      if (entryPrice > 0 && cash > 0) {
        quantity = cash / entryPrice;
        cash = 0;
        inPosition = true;
        entryTime = bars[index].timestamp;
        entryIndex = index;
      }
    } else if (!desiredLong && inPosition) {
      const exitPrice = open * (1 - costRate);
      cash = quantity * exitPrice;
      const pnl = cash - entryEquity;
      const tradeReturn = entryEquity > 0 ? pnl / entryEquity * 100 : 0;
      if (pnl >= 0) positivePnl += pnl;
      else negativePnl += Math.abs(pnl);
      trades.push({
        entryTime, exitTime: bars[index].timestamp, entryPrice, exitPrice,
        returnPct: tradeReturn, holdingBars: index - entryIndex,
      });
      quantity = 0;
      inPosition = false;
    }

    const markedEquity = inPosition ? quantity * Number(bars[index].close) : cash;
    equityCurve.push(markedEquity);
    peakEquity = Math.max(peakEquity, markedEquity);
    if (peakEquity > 0) maxDrawdown = Math.min(maxDrawdown, markedEquity / peakEquity - 1);
  }

  // Liquidate any open position at the final close so the reported final
  // equity includes exit costs and matches a fully closed historical test.
  if (inPosition) {
    const finalExitPrice = lastClose * (1 - costRate);
    cash = quantity * finalExitPrice;
    const pnl = cash - entryEquity;
    if (pnl >= 0) positivePnl += pnl;
    else negativePnl += Math.abs(pnl);
    trades.push({
      entryTime, exitTime: bars[bars.length - 1].timestamp, entryPrice,
      exitPrice: finalExitPrice, returnPct: entryEquity > 0 ? pnl / entryEquity * 100 : 0,
      holdingBars: bars.length - 1 - entryIndex,
    });
    equityCurve[equityCurve.length - 1] = cash;
    peakEquity = Math.max(peakEquity, cash);
    if (peakEquity > 0) maxDrawdown = Math.min(maxDrawdown, cash / peakEquity - 1);
  } else {
    cash = equityCurve[equityCurve.length - 1] ?? initialCapital;
  }

  // Recompute drawdown from the final marked/liquidated curve so the final
  // bar's transaction costs are reflected in both equity and peak-to-trough loss.
  peakEquity = initialCapital;
  maxDrawdown = 0;
  for (const equity of equityCurve) {
    peakEquity = Math.max(peakEquity, equity);
    if (peakEquity > 0) maxDrawdown = Math.min(maxDrawdown, equity / peakEquity - 1);
  }

  const wins = trades.filter((trade) => trade.returnPct > 0).length;
  return {
    ...empty,
    finalEquity: cash,
    netReturnPct: (cash / initialCapital - 1) * 100,
    buyHoldReturnPct: (buyHoldFinal / initialCapital - 1) * 100,
    maxDrawdownPct: Math.abs(maxDrawdown) * 100,
    closedTrades: trades.length,
    wins,
    winRatePct: trades.length ? (wins / trades.length) * 100 : null,
    profitFactor: negativePnl > 0 ? positivePnl / negativePnl : positivePnl > 0 ? null : 0,
    trades: trades.slice(-10).reverse(),
    equityCurve,
  };
}

function formatMoney(value: number, currency: string) {
  try {
    return new Intl.NumberFormat("en-IN", {
      style: "currency", currency, maximumFractionDigits: 2,
    }).format(value);
  } catch {
    return value.toFixed(2);
  }
}

function formatDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString();
}

export function StrategyBacktestPanel({
  bars,
  symbol,
  currency = "INR",
}: {
  bars: MarketBar[];
  symbol: string;
  currency?: string;
}) {
  const [shortInput, setShortInput] = useState("10");
  const [longInput, setLongInput] = useState("30");
  const [capitalInput, setCapitalInput] = useState("100000");
  const [feeInput, setFeeInput] = useState("5");
  const [slippageInput, setSlippageInput] = useState("5");

  const result = useMemo(() => runSmaCrossover(
    bars,
    Number(shortInput),
    Number(longInput),
    Number(capitalInput),
    Number(feeInput),
    Number(slippageInput),
  ), [bars, shortInput, longInput, capitalInput, feeInput, slippageInput]);
  const equityPoints = useMemo(() => {
    const values = result.equityCurve;
    if (values.length < 2) return "";
    const minimum = Math.min(...values);
    const maximum = Math.max(...values);
    const spread = maximum - minimum || 1;
    return values.map((value, index) => {
      const x = (index / (values.length - 1)) * 640;
      const y = 128 - ((value - minimum) / spread) * 104;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    }).join(" ");
  }, [result.equityCurve]);

  return (
    <section className="strategy-lab" aria-label="Historical strategy backtest">
      <div className="strategy-lab-heading">
        <div>
          <span className="strategy-lab-kicker"><FlaskConical size={13}/> HISTORICAL SIMULATION</span>
          <h3>SMA crossover backtest</h3>
          <p>{symbol} · Uses the currently loaded historical bars</p>
        </div>
        <span className="strategy-lab-data"><Activity size={13}/> {bars.length} bars</span>
      </div>

      <div className="strategy-lab-controls">
        <label>Short SMA (bars)<input type="number" min="2" max="200" step="1" value={shortInput} onChange={(event) => setShortInput(event.target.value)} /></label>
        <label>Long SMA (bars)<input type="number" min="3" max="500" step="1" value={longInput} onChange={(event) => setLongInput(event.target.value)} /></label>
        <label>Starting capital<input type="number" min="1" step="any" value={capitalInput} onChange={(event) => setCapitalInput(event.target.value)} /></label>
        <label>Fee (bps / side)<input type="number" min="0" max="4999" step="any" value={feeInput} onChange={(event) => setFeeInput(event.target.value)} /></label>
        <label>Slippage (bps / side)<input type="number" min="0" max="4999" step="any" value={slippageInput} onChange={(event) => setSlippageInput(event.target.value)} /></label>
      </div>

      {result.error ? (
        <div className="strategy-lab-error" role="status">{result.error}</div>
      ) : (
        <>
          <div className="strategy-lab-metrics">
            <div><span>Strategy final equity</span><strong>{formatMoney(result.finalEquity, currency)}</strong></div>
            <div><span>Net return</span><strong className={result.netReturnPct >= 0 ? "market-positive" : "market-negative"}>{result.netReturnPct >= 0 ? "+" : ""}{result.netReturnPct.toFixed(2)}%</strong></div>
            <div><span>Buy &amp; hold return</span><strong className={result.buyHoldReturnPct >= 0 ? "market-positive" : "market-negative"}>{result.buyHoldReturnPct >= 0 ? "+" : ""}{result.buyHoldReturnPct.toFixed(2)}%</strong></div>
            <div><span>Maximum drawdown</span><strong>{result.maxDrawdownPct.toFixed(2)}%</strong></div>
            <div><span>Closed trades</span><strong>{result.closedTrades}</strong></div>
            <div><span>Win rate</span><strong>{result.winRatePct === null ? "—" : result.winRatePct.toFixed(1) + "%"}</strong></div>
            <div><span>Profit factor</span><strong>{result.profitFactor === null || !Number.isFinite(result.profitFactor) ? "—" : result.profitFactor.toFixed(2)}</strong></div>
          </div>
          <div className="strategy-lab-equity">
            <div className="strategy-lab-trades-heading"><strong>Equity curve</strong><span>Marked to bar close; costs applied on entry/exit</span></div>
            <svg viewBox="0 0 640 145" role="img" aria-label="Historical strategy equity curve">
              {[24, 76, 128].map((y) => <line key={y} x1="0" x2="640" y1={y} y2={y} className="strategy-equity-grid" />)}
              {equityPoints && <polyline points={equityPoints} className="strategy-equity-line" fill="none" />}
            </svg>
          </div>
          <div className="strategy-lab-trades">
            <div className="strategy-lab-trades-heading"><strong>Recent closed trades</strong><span>Showing up to 10</span></div>
            {result.trades.length ? (
              <div className="strategy-lab-table-wrap">
                <table>
                  <thead><tr><th>Entry</th><th>Exit</th><th>Entry price</th><th>Exit price</th><th>Return</th><th>Bars</th></tr></thead>
                  <tbody>{result.trades.map((trade, index) => (
                    <tr key={trade.entryTime + trade.exitTime + index}>
                      <td>{formatDate(trade.entryTime)}</td>
                      <td>{formatDate(trade.exitTime)}</td>
                      <td>{formatMoney(trade.entryPrice, currency)}</td>
                      <td>{formatMoney(trade.exitPrice, currency)}</td>
                      <td className={trade.returnPct >= 0 ? "market-positive" : "market-negative"}>{trade.returnPct >= 0 ? "+" : ""}{trade.returnPct.toFixed(2)}%</td>
                      <td>{trade.holdingBars}</td>
                    </tr>
                  ))}</tbody>
                </table>
              </div>
            ) : <p>No completed crossover trades for this configuration and history window.</p>}
          </div>
        </>
      )}

      <p className="strategy-lab-disclaimer">
        Long-only SMA crossover. Signals are computed at a bar close and executed at the next bar open; an open position is liquidated at the final close. Fees and slippage are user assumptions in basis points per side. Excludes taxes, spreads beyond the entered slippage, dividends/corporate actions, market impact, liquidity, lot sizes, margin, funding, shorting and options/futures contract mechanics. Results are historical simulation only, not forecasts or investment advice. Data quality and retention depend on the selected provider.
      </p>
    </section>
  );
}

export default StrategyBacktestPanel;
