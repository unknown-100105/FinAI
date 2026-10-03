from crypto.arbitrage import estimate_arbitrage, rank_opportunities


def test_arbitrage_estimate_includes_costs():
    result = estimate_arbitrage(
        asset="BTC/USDT",
        buy_venue="venue-a",
        sell_venue="venue-b",
        capital_quote=1000,
        buy_price=100,
        sell_price=102,
        buy_fee_percent=0.1,
        sell_fee_percent=0.1,
        buy_slippage_percent=0.05,
        sell_slippage_percent=0.05,
        transfer_cost_quote=2,
        fx_cost_percent=0.1,
        tax_rate_percent=10,
    )

    assert result["quantity"] > 0
    assert result["net_profit_quote"] < 20
    assert "Simulation only" in result["execution_warning"]


def test_unprofitable_spread_is_reported():
    result = estimate_arbitrage(
        asset="BTC/USDT",
        buy_venue="a",
        sell_venue="b",
        capital_quote=1000,
        buy_price=100,
        sell_price=100.1,
        transfer_cost_quote=5,
    )

    assert result["profitable_after_costs"] is False
    assert result["net_profit_quote"] < 0


def test_rank_opportunities_by_return():
    ranked = rank_opportunities(
        [
            {"net_return_percent": -1},
            {"net_return_percent": 3},
            {"net_return_percent": 1},
        ]
    )
    assert [item["net_return_percent"] for item in ranked] == [3, 1, -1]
