from __future__ import annotations

import unittest

import pandas as pd

from src.data.data_parser import (
    NEGATIVE_POLICY_ZERO,
    aggregate_raw_quarterly_data,
)


class RawQuarterlyAggregationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = pd.DataFrame(
            {
                "transaction_date": [
                    "2024-01-10",
                    "2024-02-15",
                    "2024-04-02",
                    "2024-05-20",
                ],
                "transaction_amount": [100.0, -30.0, 50.0, -10.0],
            }
        )

    def test_net_quarterly_aggregation_is_the_default(self) -> None:
        result = aggregate_raw_quarterly_data(
            self.raw,
            date_column="transaction_date",
            amount_column="transaction_amount",
        )

        self.assertEqual(result.data["period"].astype(str).tolist(), ["2024Q1", "2024Q2"])
        self.assertEqual(result.data["demand"].tolist(), [70.0, 40.0])
        self.assertEqual(result.negative_count, 2)
        self.assertEqual(result.negative_total, -40.0)

    def test_zero_override_produces_gross_quarterly_totals(self) -> None:
        result = aggregate_raw_quarterly_data(
            self.raw,
            date_column="transaction_date",
            amount_column="transaction_amount",
            negative_policy=NEGATIVE_POLICY_ZERO,
        )

        self.assertEqual(result.data["demand"].tolist(), [100.0, 50.0])
        self.assertEqual(result.negative_count, 2)

    def test_missing_calendar_quarter_is_filled_with_zero(self) -> None:
        raw = pd.DataFrame(
            {
                "date": ["2024-01-01", "2024-07-01"],
                "amount": [10, 30],
            }
        )

        result = aggregate_raw_quarterly_data(
            raw,
            date_column="date",
            amount_column="amount",
        )

        self.assertEqual(
            result.data["period"].astype(str).tolist(),
            ["2024Q1", "2024Q2", "2024Q3"],
        )
        self.assertEqual(result.data["demand"].tolist(), [10.0, 0.0, 30.0])
        self.assertEqual(result.missing_quarters_filled, 1)

    def test_invalid_date_is_rejected(self) -> None:
        raw = pd.DataFrame({"date": ["not-a-date"], "amount": [10]})

        with self.assertRaisesRegex(ValueError, "invalid dates"):
            aggregate_raw_quarterly_data(
                raw,
                date_column="date",
                amount_column="amount",
            )

    def test_negative_net_quarter_is_rejected(self) -> None:
        raw = pd.DataFrame(
            {
                "date": ["2024-01-01", "2024-01-02"],
                "amount": [10, -20],
            }
        )

        with self.assertRaisesRegex(ValueError, "negative quarterly demand"):
            aggregate_raw_quarterly_data(
                raw,
                date_column="date",
                amount_column="amount",
            )


if __name__ == "__main__":
    unittest.main()
