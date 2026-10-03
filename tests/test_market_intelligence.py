from datetime import datetime,timedelta,timezone
import math
from market_data.models import MarketBar
from market_data.prediction import run_model_arena
from market_data.global_investments import global_catalog,eligibility

def synthetic_bars(n=180):
    bars=[]; price=100.0; start=datetime(2026,1,1,tzinfo=timezone.utc)
    for i in range(n):
        price *= 1.0 + 0.0015*math.sin(i/7.0) + (0.0008 if i%9 else -0.0012)
        bars.append(MarketBar("TEST",start+timedelta(days=i),price*.998,price*1.012,price*.988,price,100000+i*100,"test"))
    return bars

def test_model_arena_returns_multiple_auditable_models():
    result=run_model_arena(synthetic_bars(),horizon=5)
    assert result["status"]=="READY"
    assert len(result["models"])>=4
    assert result["validation"]["test_samples"]>0
    assert result["ensemble"]["direction"] in {"bullish","bearish","neutral"}

def test_global_registry_contains_major_regions_and_asset_classes():
    catalog=global_catalog()
    codes={row["country_code"] for row in catalog["countries"]}
    assert {"IN","US","GB","JP","SG","AR","ZA"}.issubset(codes)
    assert {"equity","etf","government_bond","deposit","fund"}.issubset({x["id"] for x in catalog["asset_classes"]})

def test_indian_investor_eligibility_is_explicitly_conditional_for_argentina():
    result=eligibility("AR","deposit")
    assert result["investor"]=="Indian resident individual"
    assert result["status"]=="CONDITIONAL"
    assert "FEMA" in " ".join(result["checks"])
