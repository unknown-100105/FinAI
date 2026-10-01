import unittest

from finai.portfolio.calculations import (
    asset_allocation,
    concentration_hhi,
    holding_weights,
    sector_exposure,
    top_holding_weight,
)
from finai.portfolio.models import Holding, Portfolio


class TestPortfolio(unittest.TestCase):

    def setUp(self):
        self.portfolio = Portfolio(
            holdings=(
                Holding(
                    symbol="ABC",
                    quantity=10,
                    price=100,
                    asset_class="equity",
                    sector="technology",
                ),
                Holding(
                    symbol="XYZ",
                    quantity=5,
                    price=100,
                    asset_class="debt",
                    sector="government",
                ),
            )
        )

    def test_total_value(self):
        self.assertEqual(self.portfolio.total_value, 1500)

    def test_holding_weights(self):
        weights = holding_weights(self.portfolio)

        self.assertAlmostEqual(weights["ABC"], 2 / 3)
        self.assertAlmostEqual(weights["XYZ"], 1 / 3)

    def test_asset_allocation(self):
        allocation = asset_allocation(self.portfolio)

        self.assertAlmostEqual(allocation["equity"], 2 / 3)
        self.assertAlmostEqual(allocation["debt"], 1 / 3)

    def test_sector_exposure(self):
        exposure = sector_exposure(self.portfolio)

        self.assertAlmostEqual(exposure["technology"], 2 / 3)
        self.assertAlmostEqual(exposure["government"], 1 / 3)

    def test_concentration(self):
        value = concentration_hhi(self.portfolio)

        self.assertAlmostEqual(
            value,
            (2 / 3) ** 2 + (1 / 3) ** 2,
        )

    def test_top_holding(self):
        self.assertAlmostEqual(
            top_holding_weight(self.portfolio),
            2 / 3,
        )


if __name__ == "__main__":
    unittest.main()