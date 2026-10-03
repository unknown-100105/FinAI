from knowledge.financial_catalog import build_answer, find_entries


def test_catalog_finds_mutual_funds():
    matches = find_entries("what is a mutual fund?")
    assert matches[0].topic_id == "mutual_funds"


def test_catalog_finds_money_market():
    result = build_answer("Explain the money market.")
    assert result["found"] is True
    assert "Money Market" in result["answer"]


def test_catalog_finds_post_office():
    result = build_answer("Tell me about post office schemes.")
    assert result["found"] is True
    assert result["matches"]


def test_catalog_does_not_invent_unknown_topic():
    result = build_answer("Explain xyzabc financial product.")
    assert result["found"] is False
