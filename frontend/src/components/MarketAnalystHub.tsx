import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ExternalLink,
  Newspaper,
  Pause,
  Play,
  RefreshCw,
} from "lucide-react";
import {
  explainCandle,
  getMarketAnalyst,
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

const intervals = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"];

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

export function MarketAnalystHub() {
  const [instrument, setInstrument] = useState("TCS");
  const [range, setRange] = useState("1D");
  const [interval, setInterval] = useState("5m");
  const [candles, setCandles] = useState<CandleAnalysis[]>([]);
  const [news, setNews] = useState<any[]>([]);
  const [selected, setSelected] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [playing, setPlaying] = useState(false);
  const [scenario, setScenario] = useState({
    scenarios: [] as Array<{
      name: string;
      conditions_to_watch: string[];
      not_a_prediction: boolean;
    }>,
    forecast_note: "",
  });
  const [aiExplanation, setAiExplanation] = useState("");
  const [aiBusy, setAiBusy] = useState(false);
  const [prediction, setPrediction] = useState<Prediction | null>(null);

  const rangeConfig =
    useMemo(() => ranges.find((item) => item.id === range) ?? ranges[0], [range]);

  const allowedIntervals = useMemo(() => {
    if (range === "1D") return new Set(["1m", "5m", "15m", "30m", "1h"]);
    if (range === "5D") return new Set(["1m", "5m", "15m", "30m", "1h", "4h"]);
    if (range === "1M") return new Set(["5m", "15m", "30m", "1h", "4h", "1d"]);
    return new Set(["1h", "4h", "1d"]);
  }, [range]);

  const load = async () => {
    setLoading(true);
    setError("");
    setAiExplanation("");

    try {
      const window = datesFor(rangeConfig.days);
      const result = await getMarketAnalyst(
        instrument,
        window.start,
        window.end,
        interval,
      );
      setCandles(result.analysis.candles);
      setScenario(
        result.analysis.scenario ?? {
          scenarios: [],
          forecast_note: "",
        },
      );
      setNews(result.news || []);
      setSelected(Math.max(0, result.analysis.candles.length - 1));
      try {
        const modelResult = await getPrediction(instrument, range === "1D" ? 1 : range === "5D" ? 5 : range === "1M" ? 20 : 5);
        setPrediction(modelResult);
      } catch {
        setPrediction(null);
      }
    } catch (requestError) {
      setCandles([]);
      setScenario({ scenarios: [], forecast_note: "" });
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Market analysis unavailable.",
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const next = rangeConfig.defaultInterval;
    if (!allowedIntervals.has(next)) {
      setInterval("1d");
    } else {
      setInterval(next);
    }
  }, [rangeConfig.defaultInterval, allowedIntervals]);

  useEffect(() => {
    void load();
  }, [instrument, range, interval]);

  useEffect(() => {
    if (!playing || !candles.length) return;
    const timer = window.setInterval(() => {
      setSelected((index) => (index >= candles.length - 1 ? 0 : index + 1));
    }, 700);
    return () => window.clearInterval(timer);
  }, [playing, candles.length]);

  const candle = candles[selected];
  const bars = useMemo(() => toMarketBars(candles), [candles]);
  const xaiFactors = useMemo(() => {
    const factors: Record<string, number> = {};
    for (const model of prediction?.models ?? []) {
      for (const [name, value] of Object.entries(model.feature_importance)) {
        factors[name] = (factors[name] ?? 0) + Number(value);
      }
    }
    const max = Math.max(...Object.values(factors), 0);
    return Object.entries(factors).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([name, value]) => ({
      name,
      value,
      width: max > 0 ? Math.min(100, (value / max) * 100) : 0,
    }));
  }, [prediction]);

  return (
    <section className="module-page">
      <div className="module-hero">
        <div>
          <div className="module-kicker">
            <Activity size={14} /> Market analyst
          </div>
          <h1>Explain every candle, not just the chart.</h1>
          <p>
            FinAI calculates observed OHLC anatomy, close-to-close movement,
            wick/body structure, relative volume and contextual news. Possible
            drivers are separated from proven causality.
          </p>
        </div>

        <button
          className="market-refresh"
          type="button"
          onClick={() => void load()}
          disabled={loading}
        >
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {error && <div className="module-error">{error}</div>}

      <div className="workspace-panel analyst-toolbar">
        <div className="market-search-stack">
          <MarketSearchBox value={instrument} onSelect={setInstrument} />
        </div>

        <div className="range-tabs">
          {ranges.map((item) => (
            <button
              key={item.id}
              className={range === item.id ? "active" : ""}
              type="button"
              onClick={() => setRange(item.id)}
            >
              {item.id}
            </button>
          ))}
        </div>

        <div className="range-tabs">
          {intervals.map((value) => (
            <button
              key={value}
              className={interval === value ? "active" : ""}
              type="button"
              disabled={!allowedIntervals.has(value)}
              onClick={() => setInterval(value)}
            >
              {value}
            </button>
          ))}
        </div>

        <button
          type="button"
          className="secondary-module-button"
          onClick={() => setPlaying((value) => !value)}
        >
          {playing ? <Pause size={13} /> : <Play size={13} />}
          {playing ? "Pause replay" : "Replay candles"}
        </button>
      </div>

      <section className="workspace-panel">
        <div className="module-panel-head">
          <div>
            <div className="module-kicker">OHLCV</div>
            <h2>
              {instrument} · {interval} · {candles.length} candles
            </h2>
          </div>
          <span className="source-chip">Provider snapshot</span>
        </div>

        <CandleChart
          bars={bars}
          height={390}
          selectedIndex={candle?.index}
          onSelect={setSelected}
          showVolume
        />

        <div className="analyst-slider">
          <input
            type="range"
            min="0"
            max={Math.max(0, candles.length - 1)}
            value={selected}
            onChange={(event) => setSelected(Number(event.target.value))}
          />
          <span>
            {candle ? new Date(candle.timestamp).toLocaleString() : "—"}
          </span>
        </div>
      </section>

      <section className="workspace-panel model-arena-panel">
        <div className="module-panel-head">
          <div>
            <div className="module-kicker">Multi-model intelligence</div>
            <h2>Model Arena · historical benchmark</h2>
          </div>
          <span className="source-chip">{prediction?.validation?.method || "Not run"}</span>
        </div>
        {prediction ? (
          <>
            <div className="analyst-model-summary">
              <div><span>Ensemble</span><strong>{prediction.ensemble.direction}</strong></div>
              <div><span>Probability up</span><strong>{prediction.ensemble.probability_up == null ? "—" : Math.round(prediction.ensemble.probability_up * 100) + "%"}</strong></div>
              <div><span>Agreement</span><strong>{prediction.ensemble.confidence == null ? "—" : Math.round(prediction.ensemble.confidence * 100) + "%"}</strong></div>
              <div><span>Holdout</span><strong>{prediction.validation?.test_samples || 0}</strong></div>
            </div>
            <div className="model-arena-grid">
              {prediction.models.map((model) => (
                <article key={model.model_id} className="model-arena-card">
                  <div><strong>{model.model_id.replaceAll("_", " ")}</strong><span>{model.family}</span></div>
                  <b className={model.direction === "bullish" ? "signal-positive" : model.direction === "bearish" ? "signal-negative" : "source-chip"}>{model.direction}</b>
                  <div className="model-metric-row"><span>Probability</span><strong>{model.probability_up == null ? "—" : Math.round(model.probability_up * 100) + "%"}</strong></div>
                  <div className="model-metric-row"><span>Holdout accuracy</span><strong>{model.validation_accuracy == null ? "—" : Math.round(model.validation_accuracy * 100) + "%"}</strong></div>
                  <div className="model-feature-list">{Object.entries(model.feature_importance).sort((a,b)=>b[1]-a[1]).slice(0,3).map(([name,value])=><span key={name}>{name} {Math.round(value*100)}%</span>)}</div>
                </article>
              ))}
            </div>
            <div className="data-note">The ensemble is a benchmark over chronological historical data, not a claim that any model can reliably predict future prices. Model agreement and validation metrics are shown so the user can inspect uncertainty.</div>
          </>
        ) : <div className="module-empty">Model arena unavailable or insufficient historical data.</div>}
      </section>

      <section className="workspace-panel xai-panel">
        <div className="module-panel-head">
          <div><div className="module-kicker">Explainable AI</div><h2>Why the ensemble produced this view</h2></div>
          <span className="source-chip">Feature attribution</span>
        </div>
        {xaiFactors.length ? <div className="xai-factor-grid">
          {xaiFactors.map((factor) => (
            <div key={factor.name}>
              <span>{factor.name.replaceAll("_", " ")}</span>
              <div className="xai-bar"><i style={{ width: factor.width + "%" }} /></div>
              <strong>{Math.round(factor.value * 100)}%</strong>
            </div>
          ))}
        </div> : <div className="module-empty">Run the model arena to populate explainability.</div>}
        <div className="data-note">Attribution is descriptive of the trained model features; it is not proof that a feature caused the future market move.</div>
      </section>

      <section className="workspace-panel">
        <div className="module-panel-head">
          <div>
            <div className="module-kicker">Forward scenarios</div>
            <h2>What to monitor next</h2>
          </div>
          <span className="source-chip">Not a price forecast</span>
        </div>

        <div className="scenario-grid">
          {scenario.scenarios.map((item) => (
            <article className="scenario-card" key={item.name}>
              <strong>{item.name}</strong>
              <div>
                {item.conditions_to_watch.map((condition) => (
                  <span key={condition}>• {condition}</span>
                ))}
              </div>
            </article>
          ))}
        </div>

        <div className="data-note">{scenario.forecast_note}</div>
      </section>

      <div className="analyst-grid">
        <section className="workspace-panel">
          <div className="module-panel-head">
            <div>
              <div className="module-kicker">Selected candle</div>
              <h2>
                {candle
                  ? new Date(candle.timestamp).toLocaleString()
                  : "No candle"}
              </h2>
            </div>
            <span
              className={
                candle?.direction === "bullish"
                  ? "signal-positive"
                  : candle?.direction === "bearish"
                    ? "signal-negative"
                    : "source-chip"
              }
            >
              {candle?.direction || "—"}
            </span>
          </div>

          {candle && (
            <>
              <div className="candle-fact-grid">
                {[
                  ["Open", candle.open],
                  ["High", candle.high],
                  ["Low", candle.low],
                  ["Close", candle.close],
                  [
                    "Candle return",
                    candle.return_percent == null
                      ? "—"
                      : candle.return_percent.toFixed(3) + "%",
                  ],
                  [
                    "Range",
                    candle.range_percent == null
                      ? "—"
                      : candle.range_percent.toFixed(3) + "%",
                  ],
                  ["Body / range", candle.body_percent_of_range.toFixed(1) + "%"],
                  [
                    "Upper wick / range",
                    candle.upper_wick_percent_of_range.toFixed(1) + "%",
                  ],
                  [
                    "Lower wick / range",
                    candle.lower_wick_percent_of_range.toFixed(1) + "%",
                  ],
                  [
                    "Relative volume",
                    candle.relative_volume == null
                      ? "—"
                      : candle.relative_volume.toFixed(2) + "×",
                  ],
                  ["5-candle trend", candle.trend_last_5],
                ].map(([label, value]) => (
                  <div key={String(label)}>
                    <span>{label}</span>
                    <strong>{value}</strong>
                  </div>
                ))}
              </div>

              <div className="detail-section">
                <div className="detail-section-title">What the candle shows</div>
                <div className="criteria-list">
                  {candle.observed_features.length ? (
                    candle.observed_features.map((feature) => (
                      <span key={feature}>• {feature}</span>
                    ))
                  ) : (
                    <span>No strong standalone candle-anatomy flag.</span>
                  )}
                </div>
              </div>

              <div className="data-note">
                <AlertTriangle size={12} /> {candle.causality_note}
              </div>

              <button
                type="button"
                className="primary-module-button"
                disabled={aiBusy}
                onClick={() => {
                  setAiBusy(true);
                  setAiExplanation("");
                  void explainCandle({
                    instrument,
                    candle,
                    context_news: news.slice(0, 8),
                  })
                    .then((result) =>
                      setAiExplanation(
                        result.response || "No model explanation returned.",
                      ),
                    )
                    .catch((requestError) =>
                      setAiExplanation(
                        requestError instanceof Error
                          ? requestError.message
                          : "AI explanation unavailable.",
                      ),
                    )
                    .finally(() => setAiBusy(false));
                }}
              >
                {aiBusy ? "Reasoning about candle…" : "Generate AI explanation"}
              </button>

              {aiExplanation && (
                <div className="ai-explanation">
                  <div className="detail-section-title">AI analyst note</div>
                  <p>{aiExplanation}</p>
                </div>
              )}
            </>
          )}
        </section>

        <section className="workspace-panel">
          <div className="module-panel-head">
            <div>
              <div className="module-kicker">
                <Newspaper size={12} /> Possible drivers
              </div>
              <h2>Why might this candle exist?</h2>
            </div>
            <span className="source-chip">Hypotheses, not proof</span>
          </div>

          {(candle?.possible_drivers_to_investigate ?? []).map((driver) => (
            <div key={driver} className="driver-row">
              {driver}
            </div>
          ))}

          <div className="detail-section">
            <div className="detail-section-title">Contextual news</div>
            {news.slice(0, 8).map((item: any, index: number) => (
              <a
                key={String(item.title) + index}
                className="news-item"
                href={item.link || "#"}
                target="_blank"
                rel="noreferrer"
              >
                <div>
                  <strong>{item.title}</strong>
                  <span>
                    {item.publisher || "Source"} · {item.published_at || "latest"}
                  </span>
                </div>
                <ExternalLink size={12} />
              </a>
            ))}
            {!news.length && (
              <div className="module-empty">No contextual headlines returned.</div>
            )}
          </div>
        </section>
      </div>
    </section>
  );
}

export default MarketAnalystHub;
