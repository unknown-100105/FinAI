from knowledge.investment_scope import investment_scope

def test_consolidated_scope_contains_all_major_domains():
    scope = investment_scope()
    domestic = " ".join(item for group in scope["domestic"] for item in group["items"])
    assert "Direct equity shares" in domestic
    assert "Portfolio Management Services" in domestic
    assert "Alternative Investment Funds" in domestic
    assert "Public Provident Fund" in domestic
    assert "Sovereign Gold Bonds" in domestic
    assert "Virtual Digital Assets" in domestic

def test_resident_lrs_scope():
    scope = investment_scope()
    assert scope["resident_lrs"]["annual_limit_usd"] == 250000
    assert "Foreign equities" in scope["resident_lrs"]["avenues"]

def test_regulatory_domains_cover_capital_fx_tax_retirement_aml():
    domains = {row["domain"] for row in investment_scope()["regulatory_framework"]}
    assert {"Capital markets & equities","Forex & NRI investments","Taxation","Retirement & insurance","AML & consumer safety"} <= domains

def test_vda_scope_contains_mechanics_security_and_tax():
    scope = investment_scope()
    assert "Proof of Work (PoW)" in {x["name"] for x in scope["vda_mechanics"]["consensus"]}
    assert "Proof of Stake (PoS)" in {x["name"] for x in scope["vda_mechanics"]["consensus"]}
    assert "Liquidity pull / rug pull" in scope["vda_mechanics"]["security_vectors"]
    assert "section_115BBH" in scope["vda_tax"]
    assert "section_194S" in scope["vda_tax"]
    assert "Schedule VDA" in scope["vda_tax"]["reporting"]

def test_global_registry_contains_argentina_and_major_markets():
    rows = {row["code"] for row in investment_scope()["global_market_registry"]}
    assert {"IN","US","GB","JP","SG","AR","ZA"} <= rows
    assert investment_scope()["global_example"]["country"] == "Argentina"
