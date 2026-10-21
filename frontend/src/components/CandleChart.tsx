import { useMemo, useState, type WheelEvent } from "react";
import { Minus, Plus, RotateCcw } from "lucide-react";
import type { MarketBar } from "../api/market";
import { CandleExplanationPanel } from "./CandleExplanationPanel";
import "./CandleChart.css";

function formatNumber(value: number) {
  if (!Number.isFinite(value)) return "—";
  return new Intl.NumberFormat("en-IN", { maximumFractionDigits: Math.abs(value) >= 1000 ? 2 : Math.abs(value) >= 1 ? 4 : 8 }).format(value);
}

type CandleChartProps = {
  bars: MarketBar[];
  height?: number;
  maxBars?: number;
  selectedIndex?: number;
  onSelect?: (index: number) => void;
  showVolume?: boolean;
};

export function CandleChart({
  bars,
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

  const activeIndex = selectedIndex ?? (
    inspectionIndex !== null && inspectionIndex >= 0 && inspectionIndex < bars.length
      ? inspectionIndex
      : bars.length - 1
  );

  const view = useMemo(() => {
    if (!bars.length) return [];
    const count = Math.min(visibleCount, bars.length);
    const end = Math.min(Math.max(endIndex, count - 1), bars.length - 1);
    const start = Math.max(0, end - count + 1);
    return bars.slice(start, end + 1).map((bar, index) => ({ bar, originalIndex: start + index }));
  }, [bars, visibleCount, endIndex]);

  const geometry = useMemo(() => {
    if (!view.length) return { items: [], chartWidth: 720, volumeMax: 1 };
    const highs = view.map(({ bar }) => Number(bar.high));
    const lows = view.map(({ bar }) => Number(bar.low));
    const maxPrice = Math.max(...highs);
    const minPrice = Math.min(...lows);
    const spread = maxPrice - minPrice || 1;
    const chartHeight = showVolume ? 245 : 310;
    const chartWidth = Math.max(720, view.length * 6);
    const slot = chartWidth / view.length;
    const bodyWidth = Math.max(2.1, Math.min(8, slot * 0.72));
    const items = view.map(({ bar, originalIndex }, index) => {
      const x = index * slot + slot / 2;
      const y = (value: number) => 14 + (1 - (value - minPrice) / spread) * (chartHeight - 28);
      return {
        x, high: y(bar.high), low: y(bar.low), open: y(bar.open), close: y(bar.close),
        bodyWidth, originalIndex, up: bar.close >= bar.open,
      };
    });
    const volumeValues = view.map(({ bar }) => Math.max(0, Number(bar.volume ?? 0)));
    return { items, chartWidth, volumeMax: Math.max(...volumeValues, 1) };
  }, [view, showVolume]);

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
    event.currentTarget.setPointerCapture(event.pointerId);
    setDragStart(event.clientX);
  };

  const onPointerMove = (event: React.PointerEvent<HTMLDivElement>) => {
    if (dragStart === null || !view.length) return;
    const pxPerBar = Math.max(3, event.currentTarget.clientWidth / view.length);
    const deltaBars = Math.round((dragStart - event.clientX) / pxPerBar);
    setEndIndex(Math.max(visibleCount - 1, Math.min(bars.length - 1, endIndex + deltaBars)));
  };

  const onPointerUp = () => setDragStart(null);

  if (!bars.length) {
    return <div className="candle-empty">No OHLC candles returned for this interval/range.</div>;
  }

  return (
    <div className="candle-chart" style={{ minHeight: height }}>
      <div className="candle-toolbar">
        <div className="candle-toolbar-group">
          <button type="button" onClick={() => zoom(1.4)} title="Zoom out"><Minus size={12}/></button>
          <button type="button" onClick={() => zoom(0.72)} title="Zoom in"><Plus size={12}/></button>
          <button type="button" onClick={reset} title="Reset view"><RotateCcw size={12}/></button>
        </div>
        <span>Wheel to zoom · drag to pan · select a candle to explain it</span>
        <em>{view.length} / {bars.length} candles</em>
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
          aria-label="OHLC candlestick chart. Select a candle to see its individual explanation."
        >
          <g className="candle-grid">
            {[0, 1, 2, 3, 4].map((line) => (
              <line key={line} x1="0" x2={geometry.chartWidth} y1={22 + line * 55} y2={22 + line * 55} />
            ))}
          </g>
          {geometry.items.map((candle) => (
            <g
              key={candle.originalIndex}
              className={candle.up ? "candle candle-up" : "candle candle-down"}
              onMouseEnter={() => setHoveredIndex(candle.originalIndex)}
              onMouseLeave={() => setHoveredIndex(null)}
              onClick={() => {
                setInspectionIndex(candle.originalIndex);
                onSelect?.(candle.originalIndex);
              }}
              tabIndex={0}
              role="button"
              aria-label={"Inspect candle " + (candle.originalIndex + 1)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  setInspectionIndex(candle.originalIndex);
                  onSelect?.(candle.originalIndex);
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
          {showVolume && view.map(({ bar }, index) => {
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
      {activeIndex >= 0 && <CandleExplanationPanel bars={bars} index={activeIndex} />}
    </div>
  );
}

export default CandleChart;
