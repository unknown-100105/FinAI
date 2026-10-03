import { useMemo, useRef, useState } from "react";
import type { PointerEvent as ReactPointerEvent, WheelEvent } from "react";
import type { MarketBar } from "../api/market";
import "./CandleChart.css";

type CandleChartProps = { bars: MarketBar[]; height?: number; maxBars?: number; selectedIndex?: number; onSelect?: (index: number) => void; showVolume?: boolean };

function sampleBars(bars: MarketBar[], start: number, end: number, maxBars: number) {
  const source = bars.slice(start, end);
  if (source.length <= maxBars) return source.map((bar, i) => ({ bar, originalIndex: start + i }));
  const step = source.length / maxBars;
  return Array.from({ length: maxBars }, (_, i) => {
    const offset = Math.min(source.length - 1, Math.floor(i * step));
    return { bar: source[offset], originalIndex: start + offset };
  });
}
function price(value: number) {
  return Number.isFinite(value) ? value.toLocaleString(undefined, { maximumFractionDigits: 4 }) : "—";
}

export function CandleChart({ bars, height = 360, maxBars = 520, selectedIndex, onSelect, showVolume = true }: CandleChartProps) {
  const shellRef = useRef<HTMLDivElement>(null);
  const dragRef = useRef<{ x: number; start: number; end: number } | null>(null);
  const [window, setWindow] = useState({ start: 0, end: bars.length });
  const [hover, setHover] = useState<number | null>(null);

  const effective = useMemo(() => {
    const start = Math.max(0, Math.min(window.start, Math.max(0, bars.length - 2)));
    const end = Math.max(start + 1, Math.min(window.end, bars.length));
    return sampleBars(bars, start, end, maxBars);
  }, [bars, window, maxBars]);

  const geometry = useMemo(() => {
    if (!effective.length) return { items: [], width: 900, volumeMax: 1 };
    const highs = effective.map(({ bar }) => Number(bar.high));
    const lows = effective.map(({ bar }) => Number(bar.low));
    const max = Math.max(...highs);
    const min = Math.min(...lows);
    const spread = max - min || Math.max(1, max * 0.01);
    const width = Math.max(900, effective.length * 8);
    const chartHeight = showVolume ? 250 : 310;
    const slot = width / effective.length;
    const bodyWidth = Math.max(2, Math.min(9, slot * 0.66));
    const items = effective.map(({ bar, originalIndex }, i) => {
      const x = i * slot + slot / 2;
      const y = (v: number) => 12 + (1 - (v - min) / spread) * (chartHeight - 24);
      return { x, high: y(bar.high), low: y(bar.low), open: y(bar.open), close: y(bar.close), bodyWidth, originalIndex, up: bar.close >= bar.open };
    });
    const volumes = effective.map(({ bar }) => Math.max(0, Number(bar.volume ?? 0)));
    return { items, width, volumeMax: Math.max(...volumes, 1) };
  }, [effective, showVolume]);

  const zoom = (factor: number, anchor = 0.5) => {
    if (bars.length < 2) return;
    setWindow((current) => {
      const size = current.end - current.start;
      const nextSize = Math.max(20, Math.min(bars.length, Math.round(size * factor)));
      const center = current.start + size * anchor;
      let start = Math.round(center - nextSize * anchor);
      start = Math.max(0, Math.min(start, bars.length - nextSize));
      return { start, end: start + nextSize };
    });
  };
  const reset = () => setWindow({ start: 0, end: bars.length });
  const onWheel = (event: WheelEvent<HTMLDivElement>) => {
    if (bars.length < 2) return;
    event.preventDefault();
    const rect = event.currentTarget.getBoundingClientRect();
    const anchor = rect.width ? Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width)) : 0.5;
    zoom(event.deltaY > 0 ? 1.18 : 0.84, anchor);
  };
  const onPointerDown = (event: ReactPointerEvent<HTMLDivElement>) => {
    dragRef.current = { x: event.clientX, start: window.start, end: window.end };
    event.currentTarget.setPointerCapture(event.pointerId);
  };
  const onPointerMove = (event: ReactPointerEvent<HTMLDivElement>) => {
    if (!dragRef.current || !bars.length) return;
    const rect = event.currentTarget.getBoundingClientRect();
    const pixelsPerBar = rect.width / Math.max(1, dragRef.current.end - dragRef.current.start);
    const delta = pixelsPerBar ? Math.round((dragRef.current.x - event.clientX) / pixelsPerBar) : 0;
    const size = dragRef.current.end - dragRef.current.start;
    let start = dragRef.current.start + delta;
    start = Math.max(0, Math.min(start, bars.length - size));
    setWindow({ start, end: start + size });
  };
  const toggleFullscreen = () => {
    const element = shellRef.current;
    if (!element) return;
    if (document.fullscreenElement) void document.exitFullscreen();
    else void element.requestFullscreen?.();
  };
  const hovered = hover === null ? null : bars[hover];

  if (!bars.length) return <div className="candle-empty">No OHLC candles returned for this interval/range.</div>;

  return (
    <div ref={shellRef} className="candle-chart-shell">
      <div className="candle-toolbar">
        <div className="candle-toolbar-group">
          <button type="button" onClick={() => zoom(0.7)} aria-label="Zoom in">+</button>
          <button type="button" onClick={() => zoom(1.45)} aria-label="Zoom out">−</button>
          <button type="button" onClick={reset}>Reset</button>
          <button type="button" onClick={toggleFullscreen}>Full screen</button>
        </div>
        <div className="candle-toolbar-status">
          {hovered ? [new Date(hovered.timestamp).toLocaleString(), "O " + price(hovered.open), "H " + price(hovered.high), "L " + price(hovered.low), "C " + price(hovered.close)].join(" · ") : "Wheel = zoom · Drag = pan · Click = inspect"}
        </div>
      </div>
      <div className="candle-chart" style={{ height }} onWheel={onWheel} onPointerDown={onPointerDown} onPointerMove={onPointerMove} onPointerUp={() => { dragRef.current = null; }} onPointerLeave={() => { dragRef.current = null; setHover(null); }}
        onMouseMove={(event) => {
          const rect = event.currentTarget.getBoundingClientRect();
          const index = Math.max(0, Math.min(effective.length - 1, Math.floor(((event.clientX - rect.left) / rect.width) * effective.length)));
          setHover(effective[index]?.originalIndex ?? null);
        }}>
        <div className="candle-scroll">
          <svg viewBox={"0 0 " + geometry.width + " 340"} width={geometry.width} height="340" role="img" aria-label="Interactive OHLC candlestick chart">
            <g className="candle-grid">{[0, 1, 2, 3, 4].map((line) => <line key={line} x1="0" x2={geometry.width} y1={22 + line * 55} y2={22 + line * 55} />)}</g>
            {geometry.items.map((candle) => (
              <g key={candle.originalIndex} className={candle.up ? "candle candle-up" : "candle candle-down"} onClick={() => onSelect?.(candle.originalIndex)}>
                <line x1={candle.x} x2={candle.x} y1={candle.high} y2={candle.low} className="candle-wick" vectorEffect="non-scaling-stroke" />
                <rect x={candle.x - candle.bodyWidth / 2} y={Math.min(candle.open, candle.close)} width={candle.bodyWidth} height={Math.max(2.5, Math.abs(candle.close - candle.open))} rx="0.8" className="candle-body" vectorEffect="non-scaling-stroke" />
                {selectedIndex === candle.originalIndex && <line x1={candle.x} x2={candle.x} y1="0" y2="340" className="candle-selected" vectorEffect="non-scaling-stroke" />}
                {hover === candle.originalIndex && <line x1={candle.x} x2={candle.x} y1="0" y2="340" className="candle-crosshair" vectorEffect="non-scaling-stroke" />}
              </g>
            ))}
            {showVolume && effective.map(({ bar }, index) => {
              const slot = geometry.width / effective.length;
              const width = Math.max(1.2, slot * 0.58);
              const value = Math.max(0, Number(bar.volume ?? 0));
              const barHeight = (value / geometry.volumeMax) * 72;
              return <rect key={"volume-" + index} x={index * slot + slot / 2 - width / 2} y={333 - barHeight} width={width} height={barHeight} className="candle-volume" />;
            })}
          </svg>
        </div>
        {hovered && <div className="candle-tooltip"><strong>{new Date(hovered.timestamp).toLocaleString()}</strong><span>O {price(hovered.open)} · H {price(hovered.high)}</span><span>L {price(hovered.low)} · C {price(hovered.close)}</span><span>Volume {Number(hovered.volume ?? 0).toLocaleString()}</span></div>}
      </div>
    </div>
  );
}
export default CandleChart;
