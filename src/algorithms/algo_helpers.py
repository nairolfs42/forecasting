from __future__ import annotations

import numpy as np
import pandas as pd


def centered_moving_average(demand: pd.Series, periodicity: int) -> pd.Series:
    """
    For an even periodicity, two adjacent moving averages are averaged so the
    value is centered on an observed period. For an odd periodicity, the moving
    average already has an observed period at its center.
    """
    if periodicity < 2:
        raise ValueError("periodicity must be at least 2")
    if len(demand) < periodicity + 2:
        raise ValueError(
            "not enough demand observations to deseasonalize and estimate a trend"
        )

    numeric_demand = demand.astype(float)
    trailing_average = numeric_demand.rolling(window=periodicity).mean()

    if periodicity % 2 == 0:
        left_shift = periodicity // 2 - 1
        right_shift = periodicity // 2
        return (
            trailing_average.shift(-left_shift)
            + trailing_average.shift(-right_shift)
        ) / 2.0

    return trailing_average.shift(-(periodicity // 2))


def estimate_level_and_trend(periods: pd.Series, deseasonalized_demand: pd.Series) -> tuple[float, float]:
    """Estimate ``demand = level + trend * period`` by least squares."""
    valid = deseasonalized_demand.notna()
    x = periods.loc[valid].to_numpy(dtype=float)
    y = deseasonalized_demand.loc[valid].to_numpy(dtype=float)

    if len(x) < 2:
        raise ValueError("at least two deseasonalized observations are required")

    design_matrix = np.column_stack((np.ones(len(x)), x))
    coefficients, _, _, _ = np.linalg.lstsq(design_matrix, y, rcond=None)
    level, trend = coefficients
    return float(level), float(trend)
