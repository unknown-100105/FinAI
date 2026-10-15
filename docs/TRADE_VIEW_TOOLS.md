# Trade View planning tools

The Market & Crypto Terminal now includes a local-first trade planning panel beneath the chart and technical indicators.

## Included tools

- **Saved watchlist:** add/remove symbols and select a saved symbol in the terminal. The watchlist is stored in this browser's local storage and is not synchronized to an account or server.
- **Price alert conditions:** create above/below price thresholds for the currently selected symbol. Conditions are evaluated against the latest quote state returned by the terminal. They are not background jobs, push notifications, or guaranteed real-time alerts; they only update while the terminal is running and receiving quote updates.
- **Position sizing calculator:** estimates quantity from a user-entered risk budget and absolute entry/stop distance, plus optional reward-to-risk ratio. It does not submit orders or fetch broker buying power.

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
5. Set entry, stop and risk budget; verify quantity equals floor(risk budget / abs(entry - stop)) when the stop distance and budget are positive.
6. Add a target; verify reward/risk equals abs(target - entry) / abs(entry - stop) when stop distance is positive.
7. Test at mobile width and confirm controls remain usable.
8. Disconnect or block the market API and verify the existing error/partial-feed messaging remains visible.

These checks still need to be run in a browser against the current checkout. Adding the component is not evidence that browser QA has passed.
