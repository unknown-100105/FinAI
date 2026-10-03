import crypto.mining as mining

def test_btc_mining_snapshot(monkeypatch):
    def fake_get(path):
        if path.endswith("/mining/hashrate/1d"):
            return {"currentHashrate": 100000000000000000000, "difficulty": 100}
        if path.endswith("/mining/reward-stats/144"):
            return {"totalReward": 432}
        if path.endswith("/prices"):
            return {"USD": 100000}
        if path.endswith("/mining/hashrate/pools/1m"):
            return [{"pool": "test", "share": 1}]
        raise AssertionError(path)

    monkeypatch.setattr(mining, "_get", fake_get)
    result = mining.btc_mining_snapshot(hashrate_ths=100, power_watts=1000, electricity_usd_kwh=0.10)
    assert result["status"] == "LIVE_NETWORK_SNAPSHOT"
    assert result["network_hashrate_eh_s"] == 100.0
    assert result["economics"]["expected_btc_per_day"] > 0
