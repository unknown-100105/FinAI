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
