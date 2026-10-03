from knowledge.finance_encyclopedia import build_answer

def test_history_of_money_is_covered():
    result = build_answer("What is the history of money and how did banking evolve?")
    assert result["found"] is True
    assert "History of Money" in result["answer"]


def test_crypto_mechanics_are_covered():
    result = build_answer("How does proof of work secure Bitcoin?")
    assert result["found"] is True
    assert "Proof of Work" in result["answer"]


def test_market_mechanics_are_covered():
    result = build_answer("How does an order book and price discovery work?")
    assert result["found"] is True
    assert "Order Book" in result["answer"]
