from market_data.instruments import all_instruments


def test_market_watch_contains_indian_equities():
    instruments = {item.display_name for item in all_instruments()}

    assert "TCS" in instruments
    assert "INFY" in instruments
    assert "RELIANCE" in instruments
    assert "HDFCBANK" in instruments
