import pytest

from market_data.global_investments import eligibility


def test_global_eligibility_changes_with_asset_class():
    equity = eligibility("CA", "equity")
    deposit = eligibility("CA", "deposit")

    assert equity["asset_class"] == "equity"
    assert deposit["asset_class"] == "deposit"
    assert equity["asset_class_label"] != deposit["asset_class_label"]
    assert equity["summary"] != deposit["summary"]
    assert equity["checks"] != deposit["checks"]


def test_global_eligibility_rejects_unknown_asset_class():
    with pytest.raises(ValueError, match="Unknown asset class"):
        eligibility("CA", "does_not_exist")
