import unittest

from finai.xai.risk_explanation import (
    build_risk_explanation,
    classify_risk,
)


class TestXAI(unittest.TestCase):

    def test_risk_classification(self):
        self.assertEqual(classify_risk(10), "low")
        self.assertEqual(classify_risk(50), "medium")
        self.assertEqual(classify_risk(90), "high")

    def test_driver_contributions_sum_to_one(self):
        result = build_risk_explanation(
            concentration_score=60,
            volatility_score=30,
            drawdown_score=10,
        )

        total = sum(
            driver.contribution
            for driver in result.drivers
        )

        self.assertAlmostEqual(total, 1.0)

    def test_zero_risk_input(self):
        result = build_risk_explanation(0, 0, 0)

        self.assertEqual(result.risk_score, 0)
        self.assertEqual(result.risk_level, "low")
        self.assertEqual(result.drivers, ())


if __name__ == "__main__":
    unittest.main()