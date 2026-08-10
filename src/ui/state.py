"""Mutable application state kept separate from Tkinter widgets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.algorithms.forecasts import StaticForecastResult


@dataclass
class AppState:
    source_path: Path | None = None
    output_csv_path: Path | None = None
    plot_path: Path | None = None
    raw_data: pd.DataFrame | None = None
    forecast_result: StaticForecastResult | None = None

    def clear_loaded_data(self) -> None:
        self.raw_data = None
        self.forecast_result = None

    def set_loaded_data(self, data: pd.DataFrame) -> None:
        self.raw_data = data
        self.forecast_result = None
