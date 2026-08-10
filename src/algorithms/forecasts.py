"""Forecasting methods."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.algorithms.algo_helpers import (
    centered_moving_average,
    estimate_level_and_trend,
)


@dataclass(frozen=True)
class StaticForecastResult:
    """Calculated values and fitted parameters from a static forecast."""

    data: pd.DataFrame
    level: float
    trend: float
    seasonal_factors: pd.Series


def fit_static_forecast(
    data: pd.DataFrame,
    *,
    periodicity: int = 4,
    horizon: int = 4,
) -> StaticForecastResult:
    """Fit the reference's static level/trend/seasonality forecast.

    ``data`` must be the canonical DataFrame returned by
    :func:`src.data_parser.select_forecast_columns`.
    """
    _validate_static_input(data, periodicity=periodicity, horizon=horizon)

    history = data.copy().reset_index(drop=True)
    history["t"] = np.arange(1, len(history) + 1, dtype=int)
    history["season"] = ((history["t"] - 1) % periodicity) + 1
    history["deseasonalized_demand"] = centered_moving_average(
        history["demand"], periodicity
    )

    level, trend = estimate_level_and_trend(
        history["t"], history["deseasonalized_demand"]
    )
    history["trend_demand"] = level + trend * history["t"]

    if np.isclose(history["trend_demand"], 0.0).any():
        raise ValueError("estimated trend demand contains zero; seasonal ratios fail")

    history["seasonal_ratio"] = history["demand"] / history["trend_demand"]
    seasonal_factors = (
        history.groupby("season", sort=True)["seasonal_ratio"]
        .mean()
        .rename("seasonal_factor")
    )
    history["seasonal_factor"] = history["season"].map(seasonal_factors)
    history["static_estimate"] = (
        history["trend_demand"] * history["seasonal_factor"]
    )
    history["row_type"] = "historical"

    future_t = np.arange(len(history) + 1, len(history) + horizon + 1, dtype=int)
    future_seasons = ((future_t - 1) % periodicity) + 1
    future = pd.DataFrame(
        {
            "period": _future_periods(history["period"], horizon),
            "demand": np.nan,
            "t": future_t,
            "season": future_seasons,
            "deseasonalized_demand": np.nan,
            "trend_demand": level + trend * future_t,
            "seasonal_ratio": np.nan,
            "seasonal_factor": [seasonal_factors.loc[s] for s in future_seasons],
            "row_type": "forecast",
        }
    )
    future["static_estimate"] = future["trend_demand"] * future["seasonal_factor"]

    columns = [
        "period",
        "t",
        "season",
        "demand",
        "deseasonalized_demand",
        "trend_demand",
        "seasonal_ratio",
        "seasonal_factor",
        "static_estimate",
        "row_type",
    ]
    output = pd.concat([history[columns], future[columns]], ignore_index=True)
    return StaticForecastResult(
        data=output,
        level=level,
        trend=trend,
        seasonal_factors=seasonal_factors,
    )


def _validate_static_input(
    data: pd.DataFrame, *, periodicity: int, horizon: int
) -> None:
    required = {"period", "demand"}
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"missing canonical columns: {sorted(missing)}")
    if periodicity < 2:
        raise ValueError("periodicity must be at least 2")
    if horizon < 1:
        raise ValueError("horizon must be at least 1")
    if len(data) < periodicity * 2:
        raise ValueError("static forecasting requires at least two seasonal cycles")
    #if len(data) % periodicity != 0:
    #    raise ValueError("static forecasting currently requires complete seasonal cycles")
    if data["demand"].isna().any():
        raise ValueError("demand contains missing values")


def _future_periods(periods: pd.Series, horizon: int) -> list[object]:
    """Extend simple numeric or pandas Period labels for proof-of-concept output."""
    if periods.empty:
        return list(range(1, horizon + 1))

    last = periods.iloc[-1]
    if isinstance(last, pd.Period):
        return [last + offset for offset in range(1, horizon + 1)]

    numeric = pd.to_numeric(periods, errors="coerce")
    if numeric.notna().all():
        if len(numeric) > 1:
            differences = numeric.diff().dropna()
            step = float(differences.iloc[-1])
            if not np.allclose(differences, step):
                step = 1.0
        else:
            step = 1.0
        values = [float(numeric.iloc[-1]) + step * i for i in range(1, horizon + 1)]
        if all(value.is_integer() for value in values):
            return [int(value) for value in values]
        return values

    return [f"forecast_{offset}" for offset in range(1, horizon + 1)]
