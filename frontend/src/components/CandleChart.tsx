import { useMemo } from "react";
import type { MarketBar } from "../api/market";
import "./CandleChart.css";

type CandleChartProps = {
  bars: MarketBar[];
  height?: number;
  maxBars?: number;
  selectedIndex?: number;
  onSelect?: (index: number) => void;
  showVolume?: boolean;
};

function normalize(bars: MarketBar[], maxBars: number) {
  if (bars.length <= maxBars) {
    return bars.map((bar, index) => ({ bar, originalIndex: index }));
  }
  const step = bars.length / maxBars;
  return Array.from({ length: maxBars }, (_, index) => {
    const originalIndex = Math.min(bars.length - 1, Math.floor(index * step));
    return { bar: bars[originalIndex], originalIndex };
  });
}

export function CandleChart({
  bars,
  height = 360,
  maxBars = 420,
  selectedIndex,
  onSelect,
  showVolume = true,
}: CandleChartProps) {
  const view = useMemo(() => normalize(bars, maxBars), [bars, maxBars]);

  const geometry = useMemo(() => {
    if (!view.length) {
      return { items: [], chartWidth: 720, volumeMax: 1 };
    }

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
      const y = (value: number) =>
        14 + (1 - (value - minPrice) / spread) * (chartHeight - 28);

      return {
        x,
        high: y(bar.high),
        low: y(bar.low),
        open: y(bar.open),
        close: y(bar.close),
        bodyWidth,
        originalIndex,
        up: bar.close >= bar.open,
      };
    });

    const volumeValues = view.map(({ bar }) => Math.max(0, Number(bar.volume ?? 0)));

    return {
      items,
      chartWidth,
      volumeMax: Math.max(...volumeValues, 1),
    };
  }, [view, showVolume]);

  if (!bars.length) {
    return <div className="candle-empty">No OHLC candles returned for this interval/range.</div>;
  }

  return (
    <div className="candle-chart" style={{ height }}>
      <div className="candle-scroll">
        <svg
          viewBox={"0 0 " + geometry.chartWidth + " 340"}
          width={geometry.chartWidth}
          height="340"
          role="img"
          aria-label="OHLC candlestick chart"
        >
          <g className="candle-grid">
            {[0, 1, 2, 3, 4].map((line) => (
              <line
                key={line}
                x1="0"
                x2={geometry.chartWidth}
                y1={22 + line * 55}
                y2={22 + line * 55}
              />
            ))}
          </g>

          {geometry.items.map((candle) => (
            <g
              key={candle.originalIndex}
              className={candle.up ? "candle candle-up" : "candle candle-down"}
              onClick={() => onSelect?.(candle.originalIndex)}
            >
              <line
                x1={candle.x}
                x2={candle.x}
                y1={candle.high}
                y2={candle.low}
                className="candle-wick"
                vectorEffect="non-scaling-stroke"
              />
              <rect
                x={candle.x - candle.bodyWidth / 2}
                y={Math.min(candle.open, candle.close)}
                width={candle.bodyWidth}
                height={Math.max(2.5, Math.abs(candle.close - candle.open))}
                rx="0.8"
                className="candle-body"
                vectorEffect="non-scaling-stroke"
              />
              {selectedIndex === candle.originalIndex && (
                <line
                  x1={candle.x}
                  x2={candle.x}
                  y1="0"
                  y2="340"
                  className="candle-selected"
                  vectorEffect="non-scaling-stroke"
                />
              )}
            </g>
          ))}

          {showVolume &&
            view.map(({ bar }, index) => {
              const slot = geometry.chartWidth / view.length;
              const width = Math.max(1.2, slot * 0.58);
              const value = Math.max(0, Number(bar.volume ?? 0));
              const barHeight = (value / geometry.volumeMax) * 72;
              return (
                <rect
                  key={"volume-" + index}
                  x={index * slot + slot / 2 - width / 2}
                  y={333 - barHeight}
                  width={width}
                  height={barHeight}
                  className="candle-volume"
                />
              );
            })}
        </svg>
      </div>
    </div>
  );
}

export default CandleChart;
