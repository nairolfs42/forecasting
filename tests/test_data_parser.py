from __future__ import annotations

import unittest

import pandas as pd

from src.data.data_parser import select_forecast_columns


class OptionalPeriodColumnTests(unittest.TestCase):
    def test_row_order_generates_one_based_periods(self) -> None:
        raw = pd.DataFrame(
            {
                "unused_period": [30, 10, 20],
                "demand": [8000, 13000, 23000],
            }
        )

        selected = select_forecast_columns(
            raw,
            demand_column="demand",
        )

        self.assertEqual(selected["period"].tolist(), [1, 2, 3])
        self.assertEqual(selected["demand"].tolist(), [8000.0, 13000.0, 23000.0])

    def test_explicit_period_column_still_sorts_chronologically(self) -> None:
        raw = pd.DataFrame(
            {
                "quarter": [3, 1, 2],
                "demand": [23000, 8000, 13000],
            }
        )

        selected = select_forecast_columns(
            raw,
            period_column="quarter",
            demand_column="demand",
        )

        self.assertEqual(selected["period"].tolist(), [1, 2, 3])
        self.assertEqual(selected["demand"].tolist(), [8000.0, 13000.0, 23000.0])


if __name__ == "__main__":
    unittest.main()
