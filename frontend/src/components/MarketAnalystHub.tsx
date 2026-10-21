import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  ExternalLink,
  Gauge,
  LineChart,
  Newspaper,
  Pause,
  Play,
  RefreshCw,
  ScanSearch,
  Sparkles,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import {
  explainCandle,
  getMarketAnalyst,
  getMarketModelAnalysis,
  type CandleAnalysis,
} from "../api/marketAnalyst";
import { MarketSearchBox } from "./MarketSearchBox";
import { getPrediction, type Prediction } from "../api/intelligence";
import { CandleChart } from "./CandleChart";
import type { MarketBar } from "../api/market";
import "./PlatformModules.css";

const ranges = [
  { id: "1D", days: 1, defaultInterval: "5m" },
  { id: "5D", days: 5, defaultInterval: "15m" },
  { id: "1M", days: 30, defaultInterval: "1h" },
  { id: "3M", days: 90, defaultInterval: "1d" },
  { id: "1Y", days: 365, defaultInterval: "1d" },
];

const intervals = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"] as const;

function intervalsForRange(range: string): Set<string> {
  if (range === "1D") return new Set(["1m", "5m", "15m", "30m", "1h"]);
  if (range === "5D") return new Set(["1m", "5m", "15m", "30m", "1h", "4h"]);
  if (range === "1M") return new Set(["5m", "15m", "30m", "1h", "4h", "1d"]);
  return new Set(["1h", "4h", "1d"]);
}
type Tab = "overview" | "chart" | "forecast" | "insights" | "technicals" | "patterns" | "scans" | "price-volume" | "seasonality";

const tabs: Array<[Tab, string]> = [
  ["overview", "Overview"],
  ["chart", "Chart"],
  ["forecast", "Forecast"],
  ["insights", "FinAI Insights"],
  ["technicals", "Technicals"],
  ["patterns", "Chart Patterns"],
  ["scans", "Scans"],
  ["price-volume", "Price & Volume"],
  ["seasonality", "Seasonality"],
];

function datesFor(days: number) {
  const end = new Date();
  const start = new Date();
  start.setDate(end.getDate() - days);
  return { start: start.toISOString(), end: end.toISOString() };
}

function toMarketBars(candles: CandleAnalysis[]): MarketBar[] {
  return candles.map((candle) => ({
    symbol: "",
    timestamp: candle.timestamp,
    open: candle.open,
    high: candle.high,
    low: candle.low,
    close: candle.close,
    volume: candle.volume,
    source: "analyst",
  }));
}

const num = (value: unknown, digits = 2) =>
  Number.isFinite(Number(value)) ? Number(value).toFixed(digits) : "—";

function monthEndReturns(bars: MarketBar[]) {
  const byMonth = new Map<string, number>();
  for (const bar of bars) byMonth.set(bar.timestamp.slice(0, 7), Number(bar.close));
  const months = Array.from(byMonth.keys()).sort();
  const rows: Array<{ key: string; label: string; value: number }> = [];
  for (let i = 1; i < months.length; i += 1) {
    const prev = byMonth.get(months[i - 1]);
    const current = byMonth.get(months[i]);
    if (!prev || !current) continue;
    rows.push({
      key: months[i],
      label: new Date(months[i] + "-02T00:00:00").toLocaleDateString("en-IN", { month: "short", year: "numeric" }),
      value: (current / prev - 1) * 100,
    });
  }
  return rows.slice(-12);
}

function detectPatterns(candles: CandleAnalysis[]) {
  return candles.slice(-30).flatMap((candle) => {
    const patterns: string[] = [];
    if (candle.body_percent_of_range < 12) patterns.push("Doji / indecision");
    if (candle.lower_wick_percent_of_range > 45 && candle.body_percent_of_range < 45) patterns.push("Lower-wick rejection");
    if (candle.upper_wick_percent_of_range > 45 && candle.body_percent_of_range < 45) patterns.push("Upper-wick rejection");
    if (candle.body_percent_of_range > 70 && candle.direction === "bullish") patterns.push("Strong bullish body");
    if (candle.body_percent_of_range > 70 && candle.direction === "bearish") patterns.push("Strong bearish body");
    if ((candle.relative_volume ?? 0) >= 1.8) patterns.push("Volume expansion");
    if (Math.abs(candle.return_percent ?? 0) >= 2) patterns.push("Large daily/intraday move");
    return patterns.map((name) => ({ name, timestamp: candle.timestamp, direction: candle.direction, value: candle.close }));
  });
}

function Stat({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="analyst-stat">
      <span>{label}</span>
      <strong>{value}</strong>
      {sub && <small>{sub}</small>}
    </div>
  );
}

function scoreTechnical(
  latest: CandleAnalysis | undefined,
  daily: MarketBar[],
  prediction: Prediction | null,
) {
  if (!latest || !daily.length) return 50;
  const closes = daily.map((item) => Number(item.close));
  const sma20 = closes.length >= 20 ? closes.slice(-20).reduce((a, b) => a + b, 0) / 20 : latest.close;
  const sma50 = closes.length >= 50 ? closes.slice(-50).reduce((a, b) => a + b, 0) / 50 : latest.close;
  let score = 50;
  if (latest.close > sma20) score += 9; else score -= 9;
  if (latest.close > sma50) score += 9; else score -= 9;
  if (latest.trend_last_5 === "rising") score += 8;
  if (latest.trend_last_5 === "falling") score -= 8;
  const rsi = daily.length >= 15 ? computeRsi(closes, 14) : null;
  if (rsi != null && rsi >= 50 && rsi <= 70) score += 7;
  if (rsi != null && rsi < 30) score += 4;
  if (rsi != null && rsi > 75) score -= 5;
  if (latest.relative_volume != null && latest.relative_volume >= 1.5 && latest.direction === "bullish") score += 5;
  const agreement = prediction?.ensemble?.confidence ?? 0.5;
  score += Math.round((agreement - 0.5) * 12);
  return Math.max(0, Math.min(100, Math.round(score)));
}

function computeRsi(values: number[], period: number) {
  if (values.length <= period) return null;
  const changes = values.slice(1).map((value, index) => value - values[index]);
  let gains = 0;
  let losses = 0;
  for (let i = 0; i < period; i += 1) {
    gains += Math.max(changes[i], 0);
    losses += Math.max(-changes[i], 0);
  }
  let avgGain = gains / period;
  let avgLoss = losses / period;
  for (let i = period; i < changes.length; i += 1) {
    avgGain = ((avgGain * (period - 1)) + Math.max(changes[i], 0)) / period;
    avgLoss = ((avgLoss * (period - 1)) + Math.max(-changes[i], 0)) / period;
  }
  if (avgLoss === 0) return 100;
  return 100 - 100 / (1 + avgGain / avgLoss);
}

export function MarketAnalystHub() {
  const [instrument, setInstrument] = useState("TCS");
  const [range, setRange] = useState("1D");
  const [interval, setInterval] = useState("5m");
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [candles, setCandles] = useState<CandleAnalysis[]>([]);
  const [dailyBars, setDailyBars] = useState<MarketBar[]>([]);
  const [news, setNews] = useState<any[]>([]);
  const [selected, setSelected] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [playing, setPlaying] = useState(false);
  const [scenario, setScenario] = useState<any>({ scenarios: [], forecast_note: "" });
  const [aiExplanation, setAiExplanation] = useState("");
  const [aiBusy, setAiBusy] = useState(false);
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [modelAnalysis, setModelAnalysis] = useState<any>(null);

  const rangeConfig = useMemo(() => ranges.find((item) => item.id === range) ?? ranges[0], [range]);
  const allowedIntervals = useMemo(() => intervalsForRange(range), [range]);

  const load = useCallback(async () => {
    try {
      const window = datesFor(rangeConfig.days);
      const yearWindow = datesFor(365);
      const [current, yearly] = await Promise.all([
        getMarketAnalyst(instrument, window.start, window.end, interval),
        getMarketAnalyst(instrument, yearWindow.start, yearWindow.end, "1d"),
      ]);

      setError("");
      setAiExplanation("");
      setCandles(current.analysis.candles);
      setScenario(current.analysis.scenario ?? { scenarios: [], forecast_note: "" });
      setNews(current.news || []);
      setSelected(Math.max(0, current.analysis.candles.length - 1));
      setDailyBars(toMarketBars(yearly.analysis.candles));

      try {
        const modelResult = await getPrediction(instrument, range === "1D" ? 1 : range === "5D" ? 5 : range === "1M" ? 20 : 5);
        setPrediction(modelResult);
      } catch {
        setPrediction(null);
      }

      try {
        const modelResult = await getMarketModelAnalysis(instrument, yearWindow.start, yearWindow.end, "1d");
        setModelAnalysis(modelResult.analysis);
      } catch {
        setModelAnalysis(null);
      }
    } catch (requestError) {
      setCandles([]);
      setDailyBars([]);
      setScenario({ scenarios: [], forecast_note: "" });
      setError(requestError instanceof Error ? requestError.message : "Market analysis unavailable.");
    } finally {
      setLoading(false);
    }
  }, [instrument, interval, range, rangeConfig]);

  // oxlint-disable-next-line react/set-state-in-effect -- Loads time-series and model data for the currently selected research parameters.
  useEffect(() => { void load(); }, [load]);

  useEffect(() => {
    if (!playing || !candles.length) return;
    const timer = window.setInterval(() => setSelected((index) => index >= candles.length - 1 ? 0 : index + 1), 700);
    return () => window.clearInterval(timer);
  }, [playing, candles.length]);

  const candle = candles[selected];
  const bars = useMemo(() => toMarketBars(candles), [candles]);
  const latestDaily = dailyBars.at(-1);
  const previousDaily = dailyBars.at(-2);
  const dayChange = latestDaily && previousDaily ? ((latestDaily.close / previousDaily.close) - 1) * 100 : null;
  const weekBars = dailyBars.slice(-5);
  const weekReturn = weekBars.length >= 2 ? ((weekBars.at(-1)!.close / weekBars[0].close) - 1) * 100 : null;
  const yearHigh = dailyBars.length ? Math.max(...dailyBars.map((item) => item.high)) : null;
  const yearLow = dailyBars.length ? Math.min(...dailyBars.map((item) => item.low)) : null;
  const averageVolume = dailyBars.length ? dailyBars.slice(-20).reduce((a, b) => a + Number(b.volume ?? 0), 0) / Math.max(1, Math.min(20, dailyBars.length)) : null;
  const latestVolumeRatio = latestDaily && averageVolume ? Number(latestDaily.volume ?? 0) / averageVolume : null;
  const technicalScore = useMemo(() => scoreTechnical(candle, dailyBars, prediction), [candle, dailyBars, prediction]);
  const rsi14 = dailyBars.length >= 15 ? computeRsi(dailyBars.map((item) => item.close), 14) : null;
  const closes = dailyBars.map((item) => Number(item.close));
  const sma20 = closes.length >= 20 ? closes.slice(-20).reduce((a, b) => a + b, 0) / 20 : null;
  const sma50 = closes.length >= 50 ? closes.slice(-50).reduce((a, b) => a + b, 0) / 50 : null;
  const patterns = useMemo(() => detectPatterns(candles), [candles]);
  const seasonality = useMemo(() => monthEndReturns(dailyBars), [dailyBars]);

  const strengths = [
    ...(sma20 != null && latestDaily && latestDaily.close > sma20 ? ["Price is above the 20-day moving average."] : []),
    ...(sma50 != null && latestDaily && latestDaily.close > sma50 ? ["Price is above the 50-day moving average."] : []),
    ...(dayChange != null && dayChange > 0 ? ["Latest daily session closed higher than the previous session."] : []),
    ...(latestVolumeRatio != null && latestVolumeRatio > 1.2 ? ["Recent volume is above its 20-session average."] : []),
  ];
  const weaknesses = [
    ...(sma20 != null && latestDaily && latestDaily.close < sma20 ? ["Price is below the 20-day moving average."] : []),
    ...(sma50 != null && latestDaily && latestDaily.close < sma50 ? ["Price is below the 50-day moving average."] : []),
    ...(rsi14 != null && rsi14 > 70 ? ["RSI is in an elevated zone; momentum may be extended."] : []),
    ...(dayChange != null && dayChange < 0 ? ["Latest daily session closed lower than the previous session."] : []),
  ];
  const opportunities = [
    ...(prediction?.ensemble.direction === "upside" ? ["Historical model ensemble currently leans upside."] : []),
    ...(rsi14 != null && rsi14 < 45 ? ["Momentum has room to recover if price confirms."] : []),
    ...(scenario.scenarios?.some((item: any) => String(item.name).includes("upside")) ? ["Continuation-upside conditions are being monitored."] : []),
  ];
  const risks = [
    ...(prediction?.ensemble.direction === "downside" ? ["Historical model ensemble currently leans downside."] : []),
    ...(rsi14 != null && rsi14 > 70 ? ["Momentum is elevated and may be vulnerable to reversal."] : []),
    ...(dayChange != null && dayChange < -2 ? ["Recent daily drawdown exceeds 2%."] : []),
    ...(latestVolumeRatio != null && latestVolumeRatio > 2 ? ["Volume expansion increases the importance of event/news context."] : []),
  ];

  const insightSections = [
    ["Strengths", strengths, TrendingUp],
    ["Weaknesses", weaknesses, TrendingDown],
    ["Opportunities", opportunities, Sparkles],
    ["Risks", risks, AlertTriangle],
  ] as const;

  const renderChart = () => (
    <section className="workspace-panel analyst-chart-panel">
      <div className="module-panel-head">
        <div><div className="module-kicker">OHLCV terminal</div><h2>{instrument} · {interval} · {candles.length} candles</h2></div>
        <span className="source-chip">Provider snapshot</span>
      </div>
      <CandleChart bars={bars} height={445} selectedIndex={candle?.index} onSelect={setSelected} showVolume />
      <div className="analyst-slider"><input type="range" min="0" max={Math.max(0, candles.length - 1)} value={selected} onChange={(event) => setSelected(Number(event.target.value))}/><span>{candle ? new Date(candle.timestamp).toLocaleString() : "—"}</span></div>
    </section>
  );

  return (
    <section className="module-page market-terminal-pro">
      <div className="module-hero analyst-pro-hero">
        <div>
          <div className="module-kicker"><Activity size={14} /> FinAI equity research terminal</div>
          <h1>Analyze the stock before you interpret the story.</h1>
          <p>Live/provider market data, technical analysis, historical model evidence, chart-pattern detection and investor research views — all tied to the same selected instrument.</p>
        </div>
        <button className="market-refresh" type="button" onClick={() => { setLoading(true); setError(""); setAiExplanation(""); void load(); }} disabled={loading}><RefreshCw size={14} /> {loading ? "Loading…" : "Refresh"}</button>
      </div>

      {error && <div className="module-error">{error}</div>}

      <section className="analyst-stock-head workspace-panel">
        <div className="analyst-stock-search"><MarketSearchBox value={instrument} onSelect={(nextInstrument) => { setLoading(true); setError(""); setAiExplanation(""); setInstrument(nextInstrument); }}/><div className="analyst-watchlist"><button type="button" className="active">NSE</button><span>{instrument}</span><small>FinAI research view</small></div></div>
        <div className="analyst-stock-price">
          <span>Latest session</span>
          <strong>{latestDaily ? num(latestDaily.close) : "—"}</strong>
          <em className={dayChange != null && dayChange < 0 ? "signal-negative" : "signal-positive"}>{dayChange == null ? "—" : (dayChange > 0 ? "+" : "") + num(dayChange) + "%"}</em>
        </div>
        <div className="analyst-stock-kpis">
          <Stat label="Day range" value={latestDaily ? num(latestDaily.low) + " – " + num(latestDaily.high) : "—"} />
          <Stat label="52-week range" value={yearLow != null && yearHigh != null ? num(yearLow) + " – " + num(yearHigh) : "—"} />
          <Stat label="Volume" value={latestDaily ? numberWithSuffix(latestDaily.volume) : "—"} sub={latestVolumeRatio ? num(latestVolumeRatio) + "× 20D avg" : undefined} />
          <Stat label="5-session return" value={weekReturn == null ? "—" : (weekReturn > 0 ? "+" : "") + num(weekReturn) + "%"} />
        </div>
        <div className="analyst-score">
          <span>FinAI technical score</span>
          <strong>{technicalScore}</strong><small>/100 · research signal</small>
          <div><i style={{ width: technicalScore + "%" }}/></div>
        </div>
      </section>

      <section className="workspace-panel analyst-toolbar analyst-toolbar-pro">
        <div className="market-search-stack"><span className="toolbar-label">Historical window</span><div className="range-tabs">{ranges.map((item) => <button key={item.id} className={range === item.id ? "active" : ""} type="button" onClick={() => { setRange(item.id); setInterval((current) => intervalsForRange(item.id).has(current) ? current : item.defaultInterval); setLoading(true); }}>{item.id}</button>)}</div></div>
        <div><span className="toolbar-label">Interval</span><div className="range-tabs">{intervals.map((value) => <button key={value} className={interval === value ? "active" : ""} type="button" disabled={!allowedIntervals.has(value)} onClick={() => { setInterval(value); setLoading(true); }}>{value}</button>)}</div></div>
        <button type="button" className="secondary-module-button" onClick={() => setPlaying((value) => !value)}>{playing ? <Pause size={13}/> : <Play size={13}/>} {playing ? "Pause replay" : "Replay candles"}</button>
      </section>

      <nav className="analyst-tabs" aria-label="Market analysis views">
        {tabs.map(([id, label]) => <button key={id} type="button" className={activeTab === id ? "active" : ""} onClick={() => setActiveTab(id)}>{label}</button>)}
      </nav>

      {activeTab === "overview" && (
        <>
          {renderChart()}
          <section className="analyst-card-grid four">
            <section className="workspace-panel analyst-score-card"><div className="module-kicker"><Gauge size={12}/> FinAI Essentials</div><h2>Research readiness</h2><strong>{technicalScore}%</strong><span>Technical evidence score</span><p>Based on trend, moving averages, momentum, volume and historical model agreement. It is not an investment recommendation.</p></section>
            <section className="workspace-panel"><div className="module-kicker"><TrendingUp size={12}/> Current trend</div><h2>{candle?.trend_last_5 ?? "—"}</h2><p>Latest candle: <b>{candle?.direction ?? "—"}</b>. Five-session direction is derived from OHLC closes.</p><div className="mini-stat-row"><span>RSI 14</span><strong>{rsi14 == null ? "—" : num(rsi14, 1)}</strong></div></section>
            <section className="workspace-panel"><div className="module-kicker"><BarChart3 size={12}/> Volume</div><h2>{latestVolumeRatio == null ? "—" : num(latestVolumeRatio, 2) + "×"}</h2><p>Latest daily volume versus the trailing 20-session average.</p><div className="mini-stat-row"><span>20D avg</span><strong>{numberWithSuffix(averageVolume)}</strong></div></section>
            <section className="workspace-panel"><div className="module-kicker"><ScanSearch size={12}/> Model view</div><h2>{prediction?.ensemble?.direction ?? "Not available"}</h2><p>Historical ensemble direction with model-consistency evidence.</p><div className="mini-stat-row"><span>Agreement</span><strong>{prediction?.ensemble?.confidence == null ? "—" : Math.round(prediction.ensemble.confidence * 100) + "%"}</strong></div></section>
          </section>
          <section className="workspace-panel">
            <div className="module-panel-head"><div><div className="module-kicker"><Sparkles size={12}/> Know before you invest</div><h2>Strengths · Weaknesses · Opportunities · Risks</h2></div><span className="source-chip">FinAI-derived · not external analyst consensus</span></div>
            <div className="analyst-swot-grid">{insightSections.map(([title, items, Icon]) => <article key={title}><div><Icon size={12}/><strong>{title}</strong></div>{items.length ? items.slice(0,4).map((item) => <span key={item}>• {item}</span>) : <span>• No strong signal under the current rules.</span>}</article>)}</div>
          </section>
          <section className="analyst-two-col">
            <section className="workspace-panel"><div className="module-panel-head"><div><div className="module-kicker"><LineChart size={12}/> Earnings-style context</div><h2>Price & risk ranges</h2></div></div><div className="analyst-range-visual"><div><span>52W Low</span><strong>{yearLow == null ? "—" : num(yearLow)}</strong></div><div><span>Current</span><strong>{latestDaily == null ? "—" : num(latestDaily.close)}</strong></div><div><span>52W High</span><strong>{yearHigh == null ? "—" : num(yearHigh)}</strong></div></div><div className="data-note">The current repository does not contain a verified external earnings-consensus feed, so FinAI does not fabricate analyst EPS or revenue estimates here.</div></section>
            <section className="workspace-panel"><div className="module-panel-head"><div><div className="module-kicker"><Newspaper size={12}/> Context</div><h2>Latest relevant news</h2></div></div>{news.slice(0,5).map((item,index)=><a key={String(item.title)+index} className="news-item" href={item.link || "#"} target="_blank" rel="noreferrer"><div><strong>{item.title}</strong><span>{item.publisher || "Provider"} · {item.published_at || "latest"}</span></div><ExternalLink size={11}/></a>)}</section>
          </section>
        </>
      )}

      {activeTab === "chart" && renderChart()}

      {activeTab === "forecast" && (
        <>
          <section className="workspace-panel">
            <div className="module-panel-head"><div><div className="module-kicker"><TrendingUp size={12}/> Scenario forecast</div><h2>What the historical models and rule-based scenarios say</h2></div><span className="source-chip">Not a guaranteed forecast</span></div>
            <div className="forecast-summary-grid">
              <div><span>Historical ensemble</span><strong>{modelAnalysis?.ensemble?.next_return_scenario_percent == null ? "—" : num(modelAnalysis.ensemble.next_return_scenario_percent, 3) + "%"}</strong></div>
              <div><span>Direction</span><strong>{modelAnalysis?.ensemble?.direction ?? prediction?.ensemble?.direction ?? "—"}</strong></div>
              <div><span>Model agreement</span><strong>{modelAnalysis?.ensemble?.model_agreement_percent == null ? "—" : num(modelAnalysis.ensemble.model_agreement_percent, 1) + "%"}</strong></div>
              <div><span>Reference close</span><strong>{modelAnalysis?.ensemble?.reference_last_close == null ? "—" : num(modelAnalysis.ensemble.reference_last_close)}</strong></div>
            </div>
          </section>
          <section className="workspace-panel"><div className="module-panel-head"><div><div className="module-kicker">Scenario monitor</div><h2>Conditions to watch</h2></div></div><div className="scenario-grid">{(scenario.scenarios || []).map((item:any)=><article className="scenario-card" key={item.name}><strong>{item.name}</strong>{item.conditions_to_watch.map((condition:string)=><span key={condition}>• {condition}</span>)}</article>)}</div><div className="data-note">{scenario.forecast_note}</div></section>
          <section className="workspace-panel model-ensemble-panel"><div className="module-panel-head"><div><div className="module-kicker">Quant research</div><h2>Historical model consensus</h2></div><span className="source-chip">{modelAnalysis?.method || "not run"}</span></div>{modelAnalysis?.models?.length ? <div className="model-table-wrap"><table className="model-table"><thead><tr><th>Model</th><th>MAE</th><th>Direction accuracy</th><th>Next scenario</th><th>Weight</th></tr></thead><tbody>{modelAnalysis.models.map((model:any)=><tr key={model.name}><td><strong>{model.name}</strong></td><td>{model.mae_percent == null ? "—" : num(model.mae_percent,3)+"%"}</td><td>{model.directional_accuracy_percent == null ? "—" : num(model.directional_accuracy_percent,1)+"%"}</td><td>{model.next_return_percent == null ? "—" : num(model.next_return_percent,3)+"%"}</td><td>{(Number(model.weight)*100).toFixed(1)}%</td></tr>)}</tbody></table></div> : <div className="module-empty">Historical model comparison unavailable for this window.</div>}<div className="data-note">{modelAnalysis?.warning}</div></section>
        </>
      )}

      {activeTab === "insights" && (
        <>
          <section className="workspace-panel analyst-score-banner"><div><div className="module-kicker"><Gauge size={12}/> FinAI Stock Score</div><h2>{instrument} technical research score</h2><p>This is a transparent rule-derived score from current OHLCV, trend, momentum, volume and historical model agreement.</p></div><strong>{technicalScore}<small>/100</small></strong></section>
          <div className="analyst-swot-grid analyst-swot-large">{insightSections.map(([title, items, Icon])=><article key={title}><div><Icon size={15}/><strong>{title}</strong></div>{items.length ? items.map((item)=><span key={item}>• {item}</span>) : <span>• No strong signal detected under current rules.</span>}</article>)}</div>
          <section className="workspace-panel"><div className="module-panel-head"><div><div className="module-kicker"><ShieldCheckIcon/> Decision boundary</div><h2>What this does and does not mean</h2></div></div><div className="decision-boundary"><div><b>Observed facts</b><span>Prices, OHLCV, calculated indicators and provider news.</span></div><div><b>FinAI inference</b><span>Technical score, scenario conditions and historical model consensus.</span></div><div><b>Not established</b><span>Causal explanation, guaranteed returns or an external analyst recommendation.</span></div></div></section>
        </>
      )}

      {activeTab === "technicals" && (
        <section className="workspace-panel">
          <div className="module-panel-head"><div><div className="module-kicker"><Activity size={12}/> MC-style technical workspace</div><h2>Trend, momentum and volatility</h2></div><span className="source-chip">FinAI calculations</span></div>
          <div className="analyst-technical-grid">
            <Stat label="RSI (14)" value={rsi14 == null ? "—" : num(rsi14, 1)} sub={rsi14 != null ? rsi14 > 70 ? "Elevated" : rsi14 < 30 ? "Oversold zone" : "Neutral zone" : undefined}/>
            <Stat label="SMA 20" value={sma20 == null ? "—" : num(sma20)} sub={latestDaily ? latestDaily.close > sma20! ? "Price above" : "Price below" : undefined}/>
            <Stat label="SMA 50" value={sma50 == null ? "—" : num(sma50)} sub={latestDaily ? latestDaily.close > sma50! ? "Price above" : "Price below" : undefined}/>
            <Stat label="52W position" value={latestDaily && yearLow != null && yearHigh != null ? num(((latestDaily.close - yearLow) / Math.max(1e-9, yearHigh - yearLow)) * 100,1) + "%" : "—"} sub="Range percentile"/>
            <Stat label="Max drawdown" value={modelAnalysis?.warning ? "See research" : "—"} sub="Use the Research model panel for validated historical metrics"/>
            <Stat label="Volume ratio" value={latestVolumeRatio == null ? "—" : num(latestVolumeRatio,2) + "×"} sub="Versus trailing 20 sessions"/>
          </div>
          <div className="detail-section"><div className="detail-section-title">Technical checklist</div><div className="technical-checklist">
            <div><span>Short trend</span><b>{candle?.trend_last_5 ?? "—"}</b></div>
            <div><span>Daily direction</span><b>{latestDaily && previousDaily ? latestDaily.close >= previousDaily.close ? "Bullish" : "Bearish" : "—"}</b></div>
            <div><span>Momentum zone</span><b>{rsi14 == null ? "—" : rsi14 > 70 ? "High" : rsi14 < 30 ? "Low" : "Mid-range"}</b></div>
            <div><span>Volume</span><b>{latestVolumeRatio == null ? "—" : latestVolumeRatio >= 1.5 ? "Expanded" : "Normal"}</b></div>
          </div></div>
          <div className="data-note">Indicators are mathematical transformations of price/volume data. They are not causal signals and should not be treated as certainty.</div>
        </section>
      )}

      {activeTab === "patterns" && (
        <section className="workspace-panel">
          <div className="module-panel-head"><div><div className="module-kicker"><ScanSearch size={12}/> Pattern detector</div><h2>Recent chart-pattern evidence</h2></div><span className="source-chip">Rule-based candle anatomy</span></div>
          {patterns.length ? <div className="pattern-table">{patterns.slice(-20).reverse().map((pattern, index)=><div key={pattern.name + pattern.timestamp + index}><span>{new Date(pattern.timestamp).toLocaleString()}</span><strong>{pattern.name}</strong><b>{num(pattern.value)}</b></div>)}</div> : <div className="module-empty">No strong pattern flags found in the current window.</div>}
        </section>
      )}

      {activeTab === "scans" && (
        <section className="workspace-panel">
          <div className="module-panel-head"><div><div className="module-kicker"><ScanSearch size={12}/> Technical scanner</div><h2>Current rule-based scan results</h2></div><span className="source-chip">Selected instrument</span></div>
          <div className="scan-grid-pro">
            {[
              ["Above SMA 20", sma20 != null && latestDaily ? latestDaily.close > sma20 : null, "Price versus 20-session trend"],
              ["Above SMA 50", sma50 != null && latestDaily ? latestDaily.close > sma50 : null, "Price versus 50-session trend"],
              ["RSI 30–70", rsi14 != null ? rsi14 >= 30 && rsi14 <= 70 : null, "Momentum not in extreme zone"],
              ["Volume expansion", latestVolumeRatio != null ? latestVolumeRatio >= 1.5 : null, "Latest volume ≥ 1.5× 20D average"],
              ["Five-session rising", candle ? candle.trend_last_5 === "rising" : null, "Close increased across recent 5-candle span"],
              ["Model agreement ≥ 60%", prediction?.ensemble?.confidence != null ? prediction.ensemble.confidence >= 0.6 : null, "Historical model-consistency threshold"],
            ].map(([name, passed, description])=><article key={String(name)} className={passed === true ? "passed" : passed === false ? "failed" : ""}><span>{passed === true ? "PASS" : passed === false ? "FAIL" : "—"}</span><strong>{name}</strong><p>{description}</p></article>)}
          </div>
        </section>
      )}

      {activeTab === "price-volume" && (
        <>
          <section className="workspace-panel">
            <div className="module-panel-head"><div><div className="module-kicker"><BarChart3 size={12}/> Price & volume</div><h2>{instrument} market profile</h2></div><span className="source-chip">Provider OHLCV</span></div>
            <div className="forecast-summary-grid">
              <div><span>Latest</span><strong>{latestDaily ? num(latestDaily.close) : "—"}</strong></div>
              <div><span>Day change</span><strong>{dayChange == null ? "—" : (dayChange > 0 ? "+" : "") + num(dayChange) + "%"}</strong></div>
              <div><span>Day range</span><strong>{latestDaily ? num(latestDaily.low) + "–" + num(latestDaily.high) : "—"}</strong></div>
              <div><span>20D volume ratio</span><strong>{latestVolumeRatio == null ? "—" : num(latestVolumeRatio,2) + "×"}</strong></div>
            </div>
          </section>
          {renderChart()}
        </>
      )}

      {activeTab === "seasonality" && (
        <section className="workspace-panel">
          <div className="module-panel-head"><div><div className="module-kicker"><LineChart size={12}/> Seasonality</div><h2>Recent month-end return profile</h2></div><span className="source-chip">Historical only</span></div>
          {seasonality.length ? <div className="seasonality-grid-pro">{seasonality.map((item)=><div key={item.key} className={item.value >= 0 ? "positive" : "negative"}><span>{item.label}</span><strong>{item.value >= 0 ? "+" : ""}{num(item.value,1)}%</strong><i><em style={{ width: Math.min(100, Math.abs(item.value) * 9) + "%" }}/></i></div>)}</div> : <div className="module-empty">Not enough daily history for seasonality.</div>}
          <div className="data-note">Seasonality shows historical month-end price behaviour; it is descriptive and does not imply a recurring future return.</div>
        </section>
      )}

      <section className="workspace-panel analyst-news-footer">
        <div className="module-panel-head"><div><div className="module-kicker"><Newspaper size={12}/> Contextual research</div><h2>News and possible drivers</h2></div><span className="source-chip">Hypotheses, not causality</span></div>
        <div className="analyst-news-grid">{news.slice(0,8).map((item,index)=><a key={String(item.title)+index} className="news-card" href={item.link || "#"} target="_blank" rel="noreferrer"><div className="news-card-top"><span>{item.publisher || "Provider"}</span><ExternalLink size={11}/></div><strong>{item.title}</strong><small>{item.published_at || "Latest"}</small></a>)}</div>
        <div className="data-note"><AlertTriangle size={12}/> News items are contextual evidence candidates. They do not prove that a headline caused a particular market move.</div>
      </section>

      {candle && (
        <section className="workspace-panel selected-candle-pro">
          <div className="module-panel-head"><div><div className="module-kicker">Selected candle</div><h2>{new Date(candle.timestamp).toLocaleString()} · {candle.direction}</h2></div><span className={candle.direction === "bullish" ? "signal-positive" : candle.direction === "bearish" ? "signal-negative" : "source-chip"}>{candle.direction}</span></div>
          <div className="candle-fact-grid">{[
            ["Open", candle.open], ["High", candle.high], ["Low", candle.low], ["Close", candle.close],
            ["Return", candle.return_percent == null ? "—" : num(candle.return_percent,3) + "%"],
            ["Range", candle.range_percent == null ? "—" : num(candle.range_percent,3) + "%"],
            ["Body", num(candle.body_percent_of_range,1) + "%"],
            ["Relative volume", candle.relative_volume == null ? "—" : num(candle.relative_volume,2) + "×"],
          ].map(([label,value])=><div key={String(label)}><span>{label}</span><strong>{String(value)}</strong></div>)}</div>
          <div className="detail-section"><div className="detail-section-title">Observed features</div><div className="criteria-list">{candle.observed_features.length ? candle.observed_features.map((feature)=><span key={feature}>• {feature}</span>) : <span>No strong standalone candle flag.</span>}</div></div>
          <button type="button" className="primary-module-button" disabled={aiBusy} onClick={() => { setAiBusy(true); setAiExplanation(""); void explainCandle({ instrument, candle, context_news: news.slice(0,8) }).then((result)=>setAiExplanation(result.response || "No model explanation returned.")).catch((requestError)=>setAiExplanation(requestError instanceof Error ? requestError.message : "AI explanation unavailable.")).finally(()=>setAiBusy(false)); }}>
            {aiBusy ? "Reasoning about candle…" : "Generate AI explanation"}
          </button>
          {aiExplanation && <div className="ai-explanation"><div className="detail-section-title">AI analyst note</div><p>{aiExplanation}</p></div>}
        </section>
      )}

      <div className="data-note analyst-disclaimer"><AlertTriangle size={12}/> Provider market data can be delayed or unavailable. FinAI-derived scores, patterns and scenarios are research aids, not investment advice or guaranteed forecasts.</div>
    </section>
  );
}

function numberWithSuffix(value: unknown) {
  const n = Number(value);
  if (!Number.isFinite(n)) return "—";
  if (Math.abs(n) >= 1e9) return (n / 1e9).toFixed(2) + "B";
  if (Math.abs(n) >= 1e6) return (n / 1e6).toFixed(2) + "M";
  if (Math.abs(n) >= 1e3) return (n / 1e3).toFixed(2) + "K";
  return n.toLocaleString("en-IN", { maximumFractionDigits: 0 });
}

function ShieldCheckIcon() {
  return <span className="shield-check-icon">✓</span>;
}

export default MarketAnalystHub;
