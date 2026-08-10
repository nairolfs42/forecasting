from __future__ import annotations

import unittest

import pandas as pd

from src.ui.data_table import format_table_value, prepare_dataframe_preview
from src.ui.state import AppState


class DataFramePreviewTests(unittest.TestCase):
    def test_small_dataframe_is_not_truncated(self) -> None:
        data = pd.DataFrame({"period": [1, 2], "demand": [100, 200]})
        preview, summary = prepare_dataframe_preview(data, max_rows=4)

        pd.testing.assert_frame_equal(preview, data)
        self.assertEqual(summary, "Showing all 2 rows")

    def test_large_dataframe_keeps_first_and_last_rows(self) -> None:
        data = pd.DataFrame({"period": range(1, 11)})
        preview, summary = prepare_dataframe_preview(data, max_rows=4)

        self.assertEqual(preview["period"].tolist(), [1, 2, 9, 10])
        self.assertIn("4 of 10 rows", summary)

    def test_table_value_formatting(self) -> None:
        self.assertEqual(format_table_value(float("nan")), "")
        self.assertEqual(format_table_value(1234.5), "1,234.5")
        self.assertEqual(format_table_value("2026Q1"), "2026Q1")


class AppStateTests(unittest.TestCase):
    def test_loading_new_data_clears_previous_forecast(self) -> None:
        state = AppState()
        data = pd.DataFrame({"period": [1], "demand": [100]})
        state.set_loaded_data(data)

        self.assertIs(state.raw_data, data)
        self.assertIsNone(state.forecast_result)


if __name__ == "__main__":
    unittest.main()
