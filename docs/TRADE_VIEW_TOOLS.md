# Trade View planning tools

The Market & Crypto Terminal now includes a local-first trade planning panel beneath the chart and technical indicators.

## Included tools

- **Saved watchlist:** add/remove symbols and select a saved symbol in the terminal. The watchlist is stored in this browser's local storage and is not synchronized to an account or server.
- **Price alert conditions:** create above/below price thresholds for the currently selected symbol. Conditions are evaluated against the latest quote state returned by the terminal. They are not background jobs, push notifications, or guaranteed real-time alerts; they only update while the terminal is running and receiving quote updates.
- **Position sizing calculator:** estimates quantity from a user-entered risk budget and directionally valid stop distance for a long or short position, plus an optional directionally valid reward/risk ratio. It does not submit orders or fetch broker buying power.

## Limitations

- This is a planning workspace, not a brokerage connection or order execution system.
- It does not model taxes, fees, slippage, lot size, margin, liquidity, short-sale restrictions, or broker-specific rules.
- Market quotes and chart history are provider-dependent. A displayed timestamp is provenance, not a guarantee of real-time exchange data.
- The calculator is arithmetic only and is not investment advice.
- Browser storage can be cleared or disabled. Do not store credentials or sensitive account information in it.

## Manual smoke checklist

1. Open Markets and select a supported instrument.
2. Add a second symbol to the watchlist; select it and verify the chart/search context changes.
3. Remove a watchlist symbol and reload the page; verify the remaining list persists in the same browser.
4. Add an above and below alert for the current symbol; verify each is listed and can be removed.
5. Select Long, set entry above stop, and enter a positive risk budget; verify quantity equals floor(risk budget / (entry - stop)). Select Short, set stop above entry; verify quantity equals floor(risk budget / (stop - entry)). Invalid stop direction should show no quantity.
6. For Long, set target above entry; for Short, set target below entry. Verify reward/risk equals directional reward divided by directional risk. Invalid target direction should show no ratio.
7. Test at mobile width and confirm controls remain usable.
8. Disconnect or block the market API and verify the existing error/partial-feed messaging remains visible.

These checks still need to be run in a browser against the current checkout. Adding the component is not evidence that browser QA has passed.


## Individual candle explanations

The candlestick chart now presents a deterministic explanation for the selected candle. Click or keyboard-select a candle to inspect:

- timestamp and position in the returned series;
- OHLC values, real-body size, high-low range, upper wick and lower wick;
- body-to-range percentage and close-to-previous-close percentage when available;
- volume and volume relative to up to 20 preceding candles when those observations are available;
- descriptive candidates for very small bodies/doji-like candles, long-wick candles and engulfing bodies.

Pattern labels are descriptive candidates only. They are not trade signals, forecasts, causal explanations, or evidence of profitability. Interpretation depends on instrument, interval, trend and data quality. The component does not claim that a candle predicts the next price move.

### Candle explanation manual QA

1. Load an instrument with at least 25 OHLC bars and confirm the latest candle is explained by default.
2. Select early, middle and latest candles; confirm the timestamp, ordinal and OHLC values correspond to the selected candle.
3. Check the body and wick calculations against the OHLC values.
4. Confirm change versus previous close is unavailable for the first candle and calculated for subsequent candles.
5. Confirm volume comparison uses only prior bars, excludes the selected bar, and reports unavailable when prior average volume is zero or unavailable.
6. Use keyboard Enter/Space on a focused candle and verify selection updates.
7. Test narrow mobile width, long symbol names, missing volume and partial market-data responses.
8. Verify the explanation does not generate an order, recommend a trade, or describe a pattern as a guaranteed reversal.

These checks must be run against the current checkout; adding the panel is not evidence that browser QA has passed.


## TradingView-style chart controls

The Market Terminal now includes client-side chart overlays and drawing annotations in addition to the OHLC candle inspection panel.

### Indicators
- SMA 20 and EMA 20 overlays, calculated from the returned close series.
- Bollinger Bands (20-period mean with two standard deviations).
- Volume histogram can be toggled without changing the underlying market-data request.
- Vertical and horizontal hover crosshair guides, zoom, pan, reset and fullscreen.

These calculations use only the historical bars returned by the selected provider/range. They do not guarantee exchange-grade data quality or predict future prices. EMA is initialized from the first available close; Bollinger/SMA values are shown only after 20 bars are available.

### Drawing tools
- **Horizontal level:** select the tool, then click/keyboard-select a candle; FinAI records its close as the level.
- **Trendline:** select the tool, then select two candles to anchor the line between their close values.
- Drawings are saved in browser local storage under an instrument-specific key. They are local to that browser and are not synchronized to a user account or server.
- Individual drawings can be removed, or all drawings can be cleared. Use a consistent symbol when returning to saved levels; trendlines only render when both anchor timestamps exist in the currently loaded history.

### Manual chart QA
1. Load at least 30 valid OHLC bars; confirm SMA/EMA toggles turn overlays on/off and the price scale includes the active overlay values.
2. Confirm Bollinger upper/lower bounds appear only when at least 20 valid closes exist; toggle volume and verify the price panel grows/shrinks without a network request.
3. Hover over the plot and confirm vertical candle and horizontal price guides track the pointer.
4. Select Horizontal level and select a candle; confirm the saved price equals that candle's close. Reload and confirm the level persists for the same symbol.
5. Create a trendline using two different candles; confirm it links their close prices, survives reload, and can be individually removed.
6. Change symbols and verify each symbol keeps its own drawings rather than inheriting another symbol's annotations.
7. Test zoom, drag-to-pan, reset and fullscreen with mouse and keyboard; make sure the controls remain reachable on narrow/mobile widths.
8. Test sparse/invalid provider data, missing volume, an unavailable API and long histories. Confirm the UI shows no-data/partial-feed states rather than reporting invented market values.

The current chart overlay/drawing implementation still requires the frontend build, lint, and browser checklist to be executed against the checkout before merge.
