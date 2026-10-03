from knowledge.india_finance_regulation import TOPICS, list_regulations, search_regulations

def test_listing_routes_are_present():
    ids = {item.topic_id for item in TOPICS}
    assert {"mainboard_ipo", "sme_ipo", "igp", "post_listing_fundraising", "debt_listing"} <= ids


def test_foreign_investment_routes_are_present():
    ids = {item.topic_id for item in TOPICS}
    assert {"fpi", "fdi_automatic", "fdi_government", "nri_oci", "ifsc"} <= ids


def test_crypto_and_mining_topics_are_present():
    ids = {item.topic_id for item in TOPICS}
    assert {"crypto_vda_india", "create_token", "mining"} <= ids


def test_regulatory_search_prefers_listing_topic():
    results = search_regulations("how do I list a company on the stock market")
    assert results
    assert results[0]["topic_id"] in {"mainboard_ipo", "sme_ipo", "igp", "post_listing_fundraising"}


def test_catalog_filter():
    items = list_regulations("Foreign Investment")
    assert {item["topic_id"] for item in items} >= {"fpi", "fdi_automatic", "fdi_government", "nri_oci"}
