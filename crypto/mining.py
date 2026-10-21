"""Live Bitcoin mining-network snapshot and scenario economics.

Network data source: mempool.space public REST API.
A pool's hashrate share is a network statistic, not a profitability ranking.
"""

from __future__ import annotations

from typing import Any, Dict
import requests

from policy.network_mode import assert_external_network_allowed

BASE = "https://mempool.space/api/v1"


def _get(path: str) -> Any:
    assert_external_network_allowed("mempool.space mining statistics")
    response = requests.get(BASE + path, timeout=12)
    response.raise_for_status()
    return response.json()


def btc_mining_snapshot(
    *,
    hashrate_ths: float = 200.0,
    power_watts: float = 3500.0,
    electricity_usd_kwh: float = 0.10,
) -> Dict[str, Any]:
    if hashrate_ths <= 0 or power_watts <= 0 or electricity_usd_kwh < 0:
        raise ValueError("hashrate_ths and power_watts must be positive; electricity_usd_kwh cannot be negative.")

    network = _get("/mining/hashrate/1d")
    rewards = _get("/mining/reward-stats/144")
    pools = _get("/mining/hashrate/pools/1m")
    price = _get("/prices")

    network_hashrate_hs = float(network.get("currentHashrate", 0.0))
    if network_hashrate_hs <= 0:
        raise RuntimeError("Live network hashrate is unavailable.")

    avg_reward_btc = float(rewards.get("totalReward", rewards.get("reward", 0.0))) / 144.0
    user_hashrate_hs = hashrate_ths * 1e12
    expected_btc_day = (user_hashrate_hs / network_hashrate_hs) * avg_reward_btc * 144.0
    btc_usd = float(price.get("USD", 0.0) or 0.0)

    gross_usd_day = expected_btc_day * btc_usd
    electricity_usd_day = (power_watts / 1000.0) * 24.0 * electricity_usd_kwh
    net_usd_day = gross_usd_day - electricity_usd_day

    return {
        "status": "LIVE_NETWORK_SNAPSHOT",
        "asset": "BTC",
        "network_hashrate_hs": network_hashrate_hs,
        "network_hashrate_eh_s": network_hashrate_hs / 1e18,
        "difficulty": network.get("difficulty"),
        "average_block_reward_btc_144": avg_reward_btc,
        "btc_price_usd": btc_usd,
        "miner": {
            "hashrate_ths": hashrate_ths,
            "power_watts": power_watts,
            "electricity_usd_kwh": electricity_usd_kwh,
        },
        "economics": {
            "expected_btc_per_day": expected_btc_day,
            "gross_revenue_usd_per_day": gross_usd_day,
            "electricity_cost_usd_per_day": electricity_usd_day,
            "net_before_pool_hardware_tax_usd_per_day": net_usd_day,
            "break_even_electricity_usd_kwh": (gross_usd_day / ((power_watts / 1000.0) * 24.0))
                if power_watts > 0
                else None,
        },
        "pool_snapshot": pools,
        "snapshot_source": "https://mempool.space/docs/api/rest",
        "snapshot_note": "Expected output is probabilistic; difficulty, fees, price, uptime, pool fees, hardware depreciation and downtime materially affect realized economics.",
    }
