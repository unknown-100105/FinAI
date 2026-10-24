# SwarmTrade: deterministic logical-agent planning

## Implemented baseline

The API implements a deterministic consensus simulation over up to 500 **logical** agents distributed over five fixed strategy roles: momentum, trend, mean reversion, breakout, and sentiment. Each role reads caller-supplied directional feature scores from -1 to +1. It does not call an LLM 500 times, launch 500 workers, or infer that the supplied signals came from a trained model.

Routes:

- `GET /api/v1/swarmtrade/status`: capabilities and hard safety boundaries.
- `POST /api/v1/swarmtrade/plan`: consensus, protective-level checks, cost-aware sizing, and risk-gate result.

## Example request

```json
{
  "symbol": "DEMO",
  "asset_class": "equity",
  "side": "auto",
  "entry_price": 100,
  "stop_price": 95,
  "target_price": 112,
  "capital": 100000,
  "risk_pct": 0.5,
  "fee_bps": 5,
  "slippage_bps": 5,
  "agent_count": 500,
  "signals": {
    "trend": 0.9,
    "momentum": 0.8,
    "breakout": 0.8,
    "sentiment": 0.7
  }
}
```

## Guardrails

- Maximum 500 logical votes; the consensus is deterministic and replayable.
- New-trade risk is capped at 1% of capital, regardless of larger requested risk.
- Aggregate open-position risk is limited to 3% of capital; current daily loss is checked against a configurable daily stop whose accepted maximum is 5%.
- A protective stop and target are required; invalid long/short price ordering is rejected.
- Fees and slippage are included as caller-provided assumptions. Sizing is also bounded by supplied margin and leverage assumptions.
- Options require explicit `max_loss_per_unit` per contract. Contract multiplier, unit step, margin rate and costs must be verified for the instrument and venue.
- Every response clearly reports that no order was submitted and no fill is claimed.

## Important limitations

This is a guarded **planning and simulation** baseline, not a broker-connected system or a stateful paper-trading ledger. It does not provide validated live signals, exchange-specific option Greeks/expiry/margin, futures rollover/contract specs, crypto exchange connectivity, forex pip conventions, multi-venue arbitrage execution, or performance guarantees. Those require venue-specific instrument metadata, timestamped historical data, account state, independent backtests and walk-forward evaluation. Do not use the generic sizing output as a live order instruction.

## Local checks

After pulling the branch, install the repository dependencies and run:

```powershell
python -m pytest -q tests/test_swarmtrade_engine.py
python -m pytest -q
```
