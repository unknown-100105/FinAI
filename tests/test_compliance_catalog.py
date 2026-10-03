from compliance_catalog import ITEMS, capital_gain_worksheet

def test_tax_forms_catalog_contains_core_income_tax_items():
    ids = {item.item_id for item in ITEMS}
    assert {"itr1","itr2","itr3","itr4","itr5","itr6","itr7","itr_u","itr_v","form16","form16a","form26as","ais","15g","15h","10e","67"} <= ids

def test_tax_forms_catalog_contains_gst_core_items():
    ids = {item.item_id for item in ITEMS}
    assert {"gstr1","gstr1a","gstr3b","cmp08"} <= ids

def test_capital_gain_worksheet_is_pre_tax():
    result = capital_gain_worksheet(
        buy_value=100000,
        sell_value=150000,
        transfer_costs=5000,
        improvement_cost=10000,
    )
    assert result["computed_gain_before_tax"] == 35000
