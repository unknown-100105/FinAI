import { useEffect, useMemo, useRef, useState, type WheelEvent } from "react";
import { Minus, Plus, RotateCcw, Maximize2, Minimize2, MinusCircle, TrendingUp, Activity } from "lucide-react";
import type { MarketBar } from "../api/market";
import { CandleExplanationPanel } from "./CandleExplanationPanel";
import "./CandleChart.css";

function formatNumber(value: number) {
  if (!Number.isFinite(value)) return "—";
  return new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: Math.abs(value) >= 1000 ? 2 : Math.abs(value) >= 1 ? 4 : 8,
  }).format(value);
}

type IndicatorName = "sma20" | "ema20" | "bollinger";
type DrawingMode = "horizontal" | "trendline" | null;
type Anchor = { timestamp: string; price: number };
type ChartDrawing =
  | { id: string; kind: "horizontal"; price: number; timestamp: string }
  | { id: string; kind: "trendline"; start: Anchor; end: Anchor };

type IndicatorPoint = {
  sma20: number | null;
  ema20: number | null;
  upper: number | null;
  lower: number | null;
};

type CandleChartProps = {
  bars: MarketBar[];
  symbol?: string;
  height?: number;
  maxBars?: number;
  selectedIndex?: number;
  onSelect?: (index: number) => void;
  showVolume?: boolean;
};

function drawingStorageKey(symbol: string) {
  return "finai.chart.drawings.v1:" + (symbol.trim().toUpperCase() || "UNKNOWN");
}

function readDrawings(symbol: string): ChartDrawing[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(drawingStorageKey(symbol));
    const value: unknown = raw ? JSON.parse(raw) : [];
    if (!Array.isArray(value)) return [];
    return value.filter((item): item is ChartDrawing => {
      if (!item || typeof item !== "object") return false;
      const drawing = item as Record<string, unknown>;
      if (typeof drawing.id !== "string") return false;
      if (drawing.kind === "horizontal") {
        return typeof drawing.price === "number" && Number.isFinite(drawing.price)
          && typeof drawing.timestamp === "string";
      }
      if (drawing.kind === "trendline") {
        const validAnchor = (candidate: unknown): candidate is Anchor => {
          if (!candidate || typeof candidate !== "object") return false;
          const anchor = candidate as Record<string, unknown>;
          return typeof anchor.timestamp === "string"
            && typeof anchor.price === "number"
            && Number.isFinite(anchor.price);
        };
        return validAnchor(drawing.start) && validAnchor(drawing.end);
      }
      return false;
    }).slice(-40);
  } catch {
    return [];
  }
}

function makeId() {
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
}

function buildIndicators(bars: MarketBar[]): IndicatorPoint[] {
  const result: IndicatorPoint[] = [];
  let ema: number | null = null;
  const alpha = 2 / 21;
  for (let index = 0; index < bars.length; index += 1) {
    const close = Number(bars[index].close);
    ema = Number.isFinite(close) ? (ema === null ? close : alpha * close + (1 - alpha) * ema) : ema;
    const start = Math.max(0, index - 19);
    const window = bars.slice(start, index + 1)
      .map((bar) => Number(bar.close))
      .filter(Number.isFinite);
    if (index >= 19 && window.length === 20) {
      const mean = window.reduce((sum, value) => sum + value, 0) / window.length;
      const variance = window.reduce((sum, value) => sum + (value - mean) ** 2, 0) / window.length;
      const deviation = Math.sqrt(Math.max(0, variance));
      result.push({
        sma20: mean,
        ema20: ema,
        upper: mean + 2 * deviation,
        lower: mean - 2 * deviation,
      });
    } else {
      result.push({ sma20: null, ema20: ema, upper: null, lower: null });
    }
  }
  return result;
}

export function CandleChart({
  bars,
  symbol = "UNKNOWN",
  height = 360,
  maxBars = 420,
  selectedIndex,
  onSelect,
  showVolume = true,
}: CandleChartProps) {
  const [visibleCount, setVisibleCount] = useState(Math.min(maxBars, Math.max(30, Math.min(120, bars.length || 30))));
  const [endIndex, setEndIndex] = useState(Math.max(0, bars.length - 1));
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const [inspectionIndex, setInspectionIndex] = useState<number | null>(null);
  const [dragStart, setDragStart] = useState<number | null>(null);
  const [hoverY, setHoverY] = useState<number | null>(null);
  const [volumeVisible, setVolumeVisible] = useState(showVolume);
  const dragOriginRef = useRef<{ clientX: number; endIndex: number } | null>(null);
  const [indicators, setIndicators] = useState<Record<IndicatorName, boolean>>({
    sma20: true,
    ema20: true,
    bollinger: false,
  });
  const [drawings, setDrawings] = useState<ChartDrawing[]>(() => readDrawings(symbol));
  const [drawingMode, setDrawingMode] = useState<DrawingMode>(null);
  const [pendingAnchor, setPendingAnchor] = useState<Anchor | null>(null);
  const [fullscreen, setFullscreen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const symbolKey = symbol.trim().toUpperCase() || "UNKNOWN";

  const activeIndex = selectedIndex ?? (
    inspectionIndex !== null && inspectionIndex >= 0 && inspectionIndex < bars.length
      ? inspectionIndex
      : bars.length - 1
  );

  useEffect(() => {
    const updateFullscreen = () => setFullscreen(
      typeof document !== "undefined" && document.fullscreenElement === rootRef.current,
    );
    if (typeof document !== "undefined") {
      document.addEventListener("fullscreenchange", updateFullscreen);
      return () => document.removeEventListener("fullscreenchange", updateFullscreen);
    }
  }, []);

  useEffect(() => {
    try {
      if (typeof window !== "undefined") {
        window.localStorage.setItem(drawingStorageKey(symbolKey), JSON.stringify(drawings.slice(-40)));
      }
    } catch {
      // Browser storage may be disabled; drawing tools remain usable for this view.
    }
  }, [symbolKey, drawings]);

  const view = useMemo(() => {
    if (!bars.length) return [];
    const count = Math.min(visibleCount, bars.length);
    const end = Math.min(Math.max(endIndex, count - 1), bars.length - 1);
    const start = Math.max(0, end - count + 1);
    return bars.slice(start, end + 1).map((bar, index) => ({ bar, originalIndex: start + index }));
  }, [bars, visibleCount, endIndex]);

  const indicatorSeries = useMemo(() => buildIndicators(bars), [bars]);

  const geometry = useMemo(() => {
    if (!view.length) {
      return {
        items: [] as Array<{ x: number; high: number; low: number; open: number; close: number; bodyWidth: number; originalIndex: number; up: boolean }>,
        chartWidth: 720,
        volumeMax: 1,
        slot: 1,
        startIndex: 0,
        yOf: (_value: number) => 0,
      };
    }

    const priceValues: number[] = [];
    view.forEach(({ bar, originalIndex }) => {
      priceValues.push(Number(bar.high), Number(bar.low));
      const point = indicatorSeries[originalIndex];
      if (indicators.sma20 && point?.sma20 !== null && point?.sma20 !== undefined) priceValues.push(point.sma20);
      if (indicators.ema20 && point?.ema20 !== null && point?.ema20 !== undefined) priceValues.push(point.ema20);
      if (indicators.bollinger) {
        if (point?.upper !== null && point?.upper !== undefined) priceValues.push(point.upper);
        if (point?.lower !== null && point?.lower !== undefined) priceValues.push(point.lower);
      }
    });
    const validPrices = priceValues.filter(Number.isFinite);
    const maxPrice = Math.max(...validPrices);
    const minPrice = Math.min(...validPrices);
    const spread = maxPrice - minPrice || Math.max(Math.abs(maxPrice) * 0.01, 1);
    const chartHeight = volumeVisible ? 245 : 310;
    const chartWidth = Math.max(720, view.length * 6);
    const slot = chartWidth / view.length;
    const bodyWidth = Math.max(2.1, Math.min(8, slot * 0.72));
    const yOf = (value: number) => 14 + (1 - (value - minPrice) / spread) * (chartHeight - 28);
    const items = view.map(({ bar, originalIndex }, index) => {
      const x = index * slot + slot / 2;
      return {
        x,
        high: yOf(Number(bar.high)),
        low: yOf(Number(bar.low)),
        open: yOf(Number(bar.open)),
        close: yOf(Number(bar.close)),
        bodyWidth,
        originalIndex,
        up: Number(bar.close) >= Number(bar.open),
      };
    });
    const volumeValues = view.map(({ bar }) => Math.max(0, Number(bar.volume ?? 0)));
    return {
      items,
      chartWidth,
      volumeMax: Math.max(...volumeValues, 1),
      slot,
      startIndex: view[0].originalIndex,
      yOf,
    };
  }, [view, volumeVisible, indicatorSeries, indicators]);

  const zoom = (factor: number) => {
    setVisibleCount((current) => {
      const next = Math.round(current * factor);
      return Math.min(Math.max(12, next), Math.max(12, Math.min(maxBars, bars.length)));
    });
  };

  const reset = () => {
    setVisibleCount(Math.min(maxBars, Math.max(30, Math.min(120, bars.length))));
    setEndIndex(Math.max(0, bars.length - 1));
    setInspectionIndex(null);
  };

  const onWheel = (event: WheelEvent<HTMLDivElement>) => {
    event.preventDefault();
    zoom(event.deltaY < 0 ? 0.72 : 1.4);
  };

  const onPointerDown = (event: React.PointerEvent<HTMLDivElement>) => {
    if ((event.target as HTMLElement).closest("button")) return;
    if (drawingMode) return;
    event.currentTarget.setPointerCapture(event.pointerId);
    dragOriginRef.current = { clientX: event.clientX, endIndex };
    setDragStart(event.clientX);
  };

  const onPointerMove = (event: React.PointerEvent<HTMLDivElement>) => {
    const origin = dragOriginRef.current;
    if (dragStart === null || !origin || !view.length) return;
    const pxPerBar = Math.max(3, event.currentTarget.clientWidth / view.length);
    const deltaBars = Math.round((origin.clientX - event.clientX) / pxPerBar);
    setEndIndex(Math.max(visibleCount - 1, Math.min(bars.length - 1, origin.endIndex + deltaBars)));
  };

  const onPointerUp = () => {
    dragOriginRef.current = null;
    setDragStart(null);
  };

  const selectCandle = (index: number) => {
    const bar = bars[index];
    if (!bar) return;
    if (drawingMode === "horizontal") {
      const price = Number(bar.close);
      if (Number.isFinite(price)) {
        setDrawings((current) => [...current, { id: makeId(), kind: "horizontal", price, timestamp: bar.timestamp }].slice(-40));
      }
      setDrawingMode(null);
      return;
    }
    if (drawingMode === "trendline") {
      const anchor = { timestamp: bar.timestamp, price: Number(bar.close) };
      if (!Number.isFinite(anchor.price)) return;
      if (!pendingAnchor) {
        setPendingAnchor(anchor);
      } else {
        if (pendingAnchor.timestamp !== anchor.timestamp) {
          setDrawings((current) => [...current, {
            id: makeId(), kind: "trendline", start: pendingAnchor, end: anchor,
          }].slice(-40));
        }
        setPendingAnchor(null);
        setDrawingMode(null);
      }
      return;
    }
    setInspectionIndex(index);
    onSelect?.(index);
  };

  const toggleIndicator = (name: IndicatorName) => {
    setIndicators((current) => ({ ...current, [name]: !current[name] }));
  };

  const toggleFullscreen = async () => {
    if (typeof document === "undefined" || !rootRef.current) return;
    try {
      if (document.fullscreenElement === rootRef.current) await document.exitFullscreen();
      else await rootRef.current.requestFullscreen();
    } catch {
      // Fullscreen may be blocked by browser policy; chart remains functional.
    }
  };

  const barByTimestamp = useMemo(() => {
    const result = new Map<string, number>();
    bars.forEach((bar, index) => result.set(bar.timestamp, index));
    return result;
  }, [bars]);

  const overlayPoints = (values: Array<number | null>) => geometry.items
    .map((item) => {
      const value = values[item.originalIndex];
      return value === null || value === undefined || !Number.isFinite(value)
        ? null
        : `${item.x},${geometry.yOf(value)}`;
    })
    .filter((point): point is string => point !== null)
    .join(" ");

  const renderIndicatorValues = (key: "sma20" | "ema20" | "upper" | "lower") =>
    indicatorSeries.map((point) => point[key]);

  if (!bars.length) {
    return <div className="candle-empty">No OHLC candles returned for this interval/range.</div>;
  }

  return (
    <div className={"candle-chart" + (fullscreen ? " candle-chart-fullscreen" : "")} style={{ minHeight: height }} ref={rootRef}>
      <div className="candle-toolbar">
        <div className="candle-toolbar-group">
          <button type="button" onClick={() => zoom(1.4)} title="Zoom out" aria-label="Zoom out"><Minus size={12}/></button>
          <button type="button" onClick={() => zoom(0.72)} title="Zoom in" aria-label="Zoom in"><Plus size={12}/></button>
          <button type="button" onClick={reset} title="Reset chart view" aria-label="Reset chart view"><RotateCcw size={12}/></button>
          <button type="button" onClick={() => void toggleFullscreen()} title={fullscreen ? "Exit fullscreen" : "Enter fullscreen"} aria-label={fullscreen ? "Exit fullscreen" : "Enter fullscreen"}>
            {fullscreen ? <Minimize2 size={12}/> : <Maximize2 size={12}/>}
          </button>
        </div>
        <span>Wheel to zoom · drag to pan · select candles to inspect or draw</span>
        <em>{view.length} / {bars.length} candles</em>
      </div>

      <div className="candle-tools" aria-label="Chart indicators and drawing tools">
        <span className="candle-tool-label"><Activity size={12}/> Indicators</span>
        <button type="button" className={indicators.sma20 ? "active" : ""} aria-pressed={indicators.sma20} onClick={() => toggleIndicator("sma20")}>SMA 20</button>
        <button type="button" className={indicators.ema20 ? "active" : ""} aria-pressed={indicators.ema20} onClick={() => toggleIndicator("ema20")}>EMA 20</button>
        <button type="button" className={indicators.bollinger ? "active" : ""} aria-pressed={indicators.bollinger} onClick={() => toggleIndicator("bollinger")}>Bollinger Bands</button>
        <button type="button" className={volumeVisible ? "active" : ""} aria-pressed={volumeVisible} onClick={() => setVolumeVisible((value) => !value)}>Volume</button>
        <span className="candle-tools-divider" />
        <span className="candle-tool-label"><TrendingUp size={12}/> Draw</span>
        <button type="button" className={drawingMode === "horizontal" ? "active" : ""} aria-pressed={drawingMode === "horizontal"} onClick={() => { setDrawingMode(drawingMode === "horizontal" ? null : "horizontal"); setPendingAnchor(null); }}>Horizontal level</button>
        <button type="button" className={drawingMode === "trendline" ? "active" : ""} aria-pressed={drawingMode === "trendline"} onClick={() => { setDrawingMode(drawingMode === "trendline" ? null : "trendline"); setPendingAnchor(null); }}>Trendline</button>
        <button type="button" disabled={!drawings.length} onClick={() => setDrawings([])} title="Remove all saved drawings"><MinusCircle size={12}/> Clear drawings</button>
        {drawingMode && <strong className="candle-drawing-prompt">{drawingMode === "horizontal" ? "Select a candle to place a price level" : pendingAnchor ? "Select a second candle to finish the line" : "Select first trendline anchor"}</strong>}
      </div>

      <div className={"candle-scroll " + (dragStart !== null ? "dragging" : "")}
        onWheel={onWheel}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}>
        <svg
          viewBox={"0 0 " + geometry.chartWidth + " 340"}
          width={geometry.chartWidth}
          height="340"
          role="group"
          aria-label="OHLC candlestick chart with selectable technical indicators and saved drawings."
          onMouseMove={(event) => {
            const rect = event.currentTarget.getBoundingClientRect();
            setHoverY(Math.max(0, Math.min(340, (event.clientY - rect.top) * 340 / Math.max(rect.height, 1))));
          }}
          onMouseLeave={() => setHoverY(null)}
        >
          <g className="candle-grid">
            {[0, 1, 2, 3, 4].map((line) => (
              <line key={line} x1="0" x2={geometry.chartWidth} y1={22 + line * 55} y2={22 + line * 55} />
            ))}
          </g>

          {hoverY !== null && (
            <line x1="0" x2={geometry.chartWidth} y1={hoverY} y2={hoverY} className="candle-crosshair-horizontal" vectorEffect="non-scaling-stroke" />
          )}
          {indicators.bollinger && (
            <>
              <polyline points={overlayPoints(renderIndicatorValues("upper"))} className="candle-indicator candle-bollinger" fill="none" />
              <polyline points={overlayPoints(renderIndicatorValues("lower"))} className="candle-indicator candle-bollinger" fill="none" />
            </>
          )}
          {indicators.sma20 && <polyline points={overlayPoints(renderIndicatorValues("sma20"))} className="candle-indicator candle-sma" fill="none" />}
          {indicators.ema20 && <polyline points={overlayPoints(renderIndicatorValues("ema20"))} className="candle-indicator candle-ema" fill="none" />}

          {drawings.map((drawing) => {
            if (drawing.kind === "horizontal") {
              return (
                <g key={drawing.id} className="candle-drawing">
                  <line x1="0" x2={geometry.chartWidth} y1={geometry.yOf(drawing.price)} y2={geometry.yOf(drawing.price)} className="candle-drawing-line" />
                  <text x="8" y={Math.max(10, geometry.yOf(drawing.price) - 4)} className="candle-drawing-label">{formatNumber(drawing.price)}</text>
                </g>
              );
            }
            const startIndex = barByTimestamp.get(drawing.start.timestamp);
            const endIndexForLine = barByTimestamp.get(drawing.end.timestamp);
            if (startIndex === undefined || endIndexForLine === undefined) return null;
            const x1 = (startIndex - geometry.startIndex) * geometry.slot + geometry.slot / 2;
            const x2 = (endIndexForLine - geometry.startIndex) * geometry.slot + geometry.slot / 2;
            return (
              <line key={drawing.id} x1={x1} y1={geometry.yOf(drawing.start.price)} x2={x2} y2={geometry.yOf(drawing.end.price)} className="candle-drawing-line candle-trendline" />
            );
          })}

          {geometry.items.map((candle) => (
            <g
              key={candle.originalIndex}
              className={candle.up ? "candle candle-up" : "candle candle-down"}
              onMouseEnter={() => setHoveredIndex(candle.originalIndex)}
              onMouseLeave={() => setHoveredIndex(null)}
              onClick={() => selectCandle(candle.originalIndex)}
              tabIndex={0}
              role="button"
              aria-label={"Inspect/draw on candle " + (candle.originalIndex + 1)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  selectCandle(candle.originalIndex);
                }
              }}
            >
              <line x1={candle.x} x2={candle.x} y1={candle.high} y2={candle.low} className="candle-wick" vectorEffect="non-scaling-stroke" />
              <rect
                x={candle.x - candle.bodyWidth / 2}
                y={Math.min(candle.open, candle.close)}
                width={candle.bodyWidth}
                height={Math.max(2.5, Math.abs(candle.close - candle.open))}
                rx="0.8"
                className="candle-body"
                vectorEffect="non-scaling-stroke"
              />
              {activeIndex === candle.originalIndex && (
                <line x1={candle.x} x2={candle.x} y1="0" y2="340" className="candle-selected" vectorEffect="non-scaling-stroke" />
              )}
            </g>
          ))}

          {hoveredIndex !== null && bars[hoveredIndex] && (
            <line
              x1={geometry.items.find((item) => item.originalIndex === hoveredIndex)?.x ?? 0}
              x2={geometry.items.find((item) => item.originalIndex === hoveredIndex)?.x ?? 0}
              y1="0" y2="340" className="candle-hover-line" vectorEffect="non-scaling-stroke"
            />
          )}
          {volumeVisible && view.map(({ bar }, index) => {
            const slot = geometry.chartWidth / view.length;
            const width = Math.max(1.2, slot * 0.58);
            const value = Math.max(0, Number(bar.volume ?? 0));
            const barHeight = (value / geometry.volumeMax) * 72;
            return <rect key={"volume-" + index} x={index * slot + slot / 2 - width / 2} y={333 - barHeight} width={width} height={barHeight} className="candle-volume" />;
          })}
        </svg>

        {hoveredIndex !== null && bars[hoveredIndex] && (
          <div className="candle-hover-details">
            <strong>{new Date(bars[hoveredIndex].timestamp).toLocaleString()}</strong>
            <span>O {formatNumber(Number(bars[hoveredIndex].open))}</span>
            <span>H {formatNumber(Number(bars[hoveredIndex].high))}</span>
            <span>L {formatNumber(Number(bars[hoveredIndex].low))}</span>
            <span>C {formatNumber(Number(bars[hoveredIndex].close))}</span>
            <span>V {formatNumber(Number(bars[hoveredIndex].volume ?? 0))}</span>
          </div>
        )}
      </div>

      {drawings.length > 0 && (
        <div className="candle-drawing-list" aria-label="Saved chart drawings">
          {drawings.map((drawing) => (
            <div key={drawing.id}>
              <span>{drawing.kind === "horizontal"
                ? "Horizontal level · " + formatNumber(drawing.price)
                : "Trendline · " + formatNumber(drawing.start.price) + " → " + formatNumber(drawing.end.price)}</span>
              <button type="button" onClick={() => setDrawings((current) => current.filter((item) => item.id !== drawing.id))} aria-label="Remove drawing">Remove</button>
            </div>
          ))}
        </div>
      )}
      {activeIndex >= 0 && <CandleExplanationPanel bars={bars} index={activeIndex} />}
    </div>
  );
}

export default CandleChart;
