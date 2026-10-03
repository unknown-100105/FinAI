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
  getMarketModelAnalysis,
  type CandleAnalysis,
} from "../api/marketAnalyst";
import { MarketSearchBox } from "./MarketSearchBox";
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
  const [modelAnalysis, setModelAnalysis] = useState<any>(null);
  const [modelBusy, setModelBusy] = useState(false);

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
    setModelBusy(true);

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

      const modelResult = await getMarketModelAnalysis(
        instrument,
        window.start,
        window.end,
        interval,
      );
      setModelAnalysis(modelResult.analysis);
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
      setModelBusy(false);
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

      <section className="workspace-panel model-ensemble-panel">
        <div className="module-panel-head">
          <div>
            <div className="module-kicker">Quant research ensemble</div>
            <h2>Walk-forward model comparison</h2>
          </div>
          <span className="source-chip">Research scenarios · not guarantees</span>
        </div>
        <p className="data-note">FinAI does not assume one model is universally best. It evaluates multiple model families on the selected historical window and combines them using inverse backtest error. The result is a research scenario, not a guaranteed forecast.</p>
        {modelBusy ? <div className="module-empty">Running walk-forward model evaluation…</div> : modelAnalysis?.ensemble ? (
          <>
            <div className="forecast-summary-grid">
              <div><span>Ensemble next-return scenario</span><strong>{Number(modelAnalysis.ensemble.next_return_scenario_percent).toFixed(3)}%</strong></div>
              <div><span>Scenario direction</span><strong>{modelAnalysis.ensemble.direction}</strong></div>
              <div><span>Model agreement</span><strong>{Number(modelAnalysis.ensemble.model_agreement_percent).toFixed(1)}%</strong></div>
              <div><span>Reference close</span><strong>{Number(modelAnalysis.ensemble.reference_last_close).toFixed(2)}</strong></div>
            </div>
            <div className="model-table-wrap">
              <table className="model-table">
                <thead><tr><th>Model</th><th>Backtest MAE</th><th>Direction accuracy</th><th>Next scenario</th><th>Weight</th></tr></thead>
                <tbody>{(modelAnalysis.models || []).map((model:any) => (
                  <tr key={model.name}>
                    <td><strong>{model.name}</strong></td>
                    <td>{model.mae_percent == null ? "—" : Number(model.mae_percent).toFixed(3) + "%"}</td>
                    <td>{model.directional_accuracy_percent == null ? "—" : Number(model.directional_accuracy_percent).toFixed(1) + "%"}</td>
                    <td>{model.next_return_percent == null ? "—" : Number(model.next_return_percent).toFixed(3) + "%"}</td>
                    <td>{(Number(model.weight) * 100).toFixed(1)}%</td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
          </>
        ) : <div className="module-empty">{modelAnalysis?.message || "No model comparison available for this history window."}</div>}
        <div className="data-note">{modelAnalysis?.warning || "Use the model panel as research evidence, not as a promise about the next market move."}</div>
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
