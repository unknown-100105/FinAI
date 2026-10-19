import type { MarketBar } from "../api/market";

function fmt(value: number): string {
  if (!Number.isFinite(value)) return "—";
  return new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: Math.abs(value) >= 1000 ? 2 : Math.abs(value) >= 1 ? 4 : 8,
  }).format(value);
}

type CandleExplanationPanelProps = {
  bars: MarketBar[];
  index: number;
};

export function CandleExplanationPanel({ bars, index }: CandleExplanationPanelProps) {
  const bar = bars[index];
  if (!bar) return null;

  const previous = index > 0 ? bars[index - 1] : undefined;
  const valuesAreFinite = [bar.open, bar.high, bar.low, bar.close].every(Number.isFinite);
  const validOhlc = valuesAreFinite
    && bar.high >= Math.max(bar.open, bar.close)
    && bar.low <= Math.min(bar.open, bar.close)
    && bar.high >= bar.low;
  const range = validOhlc ? bar.high - bar.low : Number.NaN;
  const body = valuesAreFinite ? Math.abs(bar.close - bar.open) : Number.NaN;
  const upperWick = validOhlc ? Math.max(0, bar.high - Math.max(bar.open, bar.close)) : Number.NaN;
  const lowerWick = validOhlc ? Math.max(0, Math.min(bar.open, bar.close) - bar.low) : Number.NaN;
  const bodyPct = validOhlc && range > 0 ? (body / range) * 100 : Number.NaN;
  const change = previous
    && Number.isFinite(previous.close)
    && Number.isFinite(bar.close)
    && previous.close !== 0
    ? ((bar.close / previous.close) - 1) * 100
    : null;

  // Missing volume is not the same thing as zero volume. Exclude missing values
  // from the prior-bar baseline and do not calculate a ratio if current volume is absent.
  const recentVolumes = bars.slice(Math.max(0, index - 20), index)
    .map((item) => item.volume)
    .filter((value): value is number => value != null && Number.isFinite(value) && value >= 0);
  const avgVolume = recentVolumes.length
    ? recentVolumes.reduce((sum, value) => sum + value, 0) / recentVolumes.length
    : null;
  const volumeNow = bar.volume != null && Number.isFinite(bar.volume) && bar.volume >= 0
    ? bar.volume
    : null;
  const volumeRatio = volumeNow != null && avgVolume != null && avgVolume > 0
    ? volumeNow / avgVolume
    : null;

  const bullish = validOhlc && bar.close > bar.open;
  const bearish = validOhlc && bar.close < bar.open;
  const direction = !validOhlc
    ? "OHLC data needs checking"
    : bullish ? "Bullish close" : bearish ? "Bearish close" : "Flat close";
  const patternNotes: string[] = [];

  if (!validOhlc) {
    patternNotes.push("This candle has missing, non-finite, or inconsistent OHLC values. Pattern interpretation is withheld until the market-data source is checked.");
  } else {
    if (range === 0 || body <= range * 0.1) {
      patternNotes.push("Doji / very small body: open and close are close relative to this candle's range. This can reflect indecision, but is not a direction signal by itself.");
    } else if (lowerWick >= body * 2 && upperWick <= body * 1.2) {
      patternNotes.push("Long lower-wick candle: price traded lower but recovered before close. This can indicate rejection of lower prices; confirmation and surrounding trend matter.");
    } else if (upperWick >= body * 2 && lowerWick <= body * 1.2) {
      patternNotes.push("Long upper-wick candle: price traded higher but fell back before close. This can indicate rejection of higher prices; confirmation and surrounding trend matter.");
    }

    if (previous && [previous.open, previous.close].every(Number.isFinite)) {
      const prevBullish = previous.close > previous.open;
      const prevBearish = previous.close < previous.open;
      const currentTop = Math.max(bar.open, bar.close);
      const currentBottom = Math.min(bar.open, bar.close);
      const previousTop = Math.max(previous.open, previous.close);
      const previousBottom = Math.min(previous.open, previous.close);
      if (bullish && prevBearish && currentBottom <= previousBottom && currentTop >= previousTop) {
        patternNotes.push("Bullish engulfing candidate: this candle's real body covers the previous bearish real body. It is a pattern candidate, not proof of reversal.");
      } else if (bearish && prevBullish && currentBottom <= previousBottom && currentTop >= previousTop) {
        patternNotes.push("Bearish engulfing candidate: this candle's real body covers the previous bullish real body. It is a pattern candidate, not proof of reversal.");
      }
    }

    if (!patternNotes.length) {
      patternNotes.push(
        bullish
          ? "The close is above the open, so the candle finished higher than it began. The wick lengths show how far price moved away from the closing area."
          : bearish
            ? "The close is below the open, so the candle finished lower than it began. The wick lengths show how far price moved away from the closing area."
            : "The open equals the close, so there is no net body direction. The high-low range still shows the period's price excursion.",
      );
    }
  }

  const timestamp = new Date(bar.timestamp);
  const timestampLabel = Number.isNaN(timestamp.getTime())
    ? "Timestamp unavailable"
    : timestamp.toLocaleString();

  return (
    <section className="candle-explanation" aria-live="polite" aria-label="Selected candle explanation">
      <div className="candle-explanation-heading">
        <div>
          <span>INDIVIDUAL CANDLE EXPLANATION · {index + 1} OF {bars.length}</span>
          <strong>{timestampLabel}</strong>
        </div>
        <b className={bullish ? "market-positive" : bearish ? "market-negative" : ""}>{direction}</b>
      </div>
      <div className="candle-explanation-values">
        <div><span>Open</span><strong>{fmt(bar.open)}</strong></div>
        <div><span>High</span><strong>{fmt(bar.high)}</strong></div>
        <div><span>Low</span><strong>{fmt(bar.low)}</strong></div>
        <div><span>Close</span><strong>{fmt(bar.close)}</strong></div>
        <div><span>Body</span><strong>{fmt(body)}</strong></div>
        <div><span>Range</span><strong>{fmt(range)}</strong></div>
        <div><span>Upper wick</span><strong>{fmt(upperWick)}</strong></div>
        <div><span>Lower wick</span><strong>{fmt(lowerWick)}</strong></div>
        <div><span>Body / range</span><strong>{Number.isFinite(bodyPct) ? bodyPct.toFixed(1) + "%" : "Not available"}</strong></div>
        <div><span>Volume</span><strong>{volumeNow == null ? "Not supplied" : fmt(volumeNow)}</strong></div>
        <div><span>Change vs previous close</span><strong>{change == null ? "Not available" : (change >= 0 ? "+" : "") + change.toFixed(2) + "%"}</strong></div>
        <div><span>Volume vs prior average</span><strong>{volumeRatio == null ? "Not available" : volumeRatio.toFixed(2) + "×"}</strong></div>
      </div>
      <div className="candle-explanation-notes">
        {patternNotes.map((note) => <p key={note}>{note}</p>)}
        <p className="candle-explanation-caveat">
          Interpretation is deterministic and descriptive, not a forecast or trading instruction. Candlestick patterns are context-dependent; this panel does not establish causality or profitability. Volume comparison uses available volume from up to 20 preceding candles and excludes the selected candle.
        </p>
      </div>
    </section>
  );
}
