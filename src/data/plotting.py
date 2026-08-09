"""Matplotlib output for forecast results."""

from __future__ import annotations
from pathlib import Path
from src.algorithms.forecasts import StaticForecastResult


def plot_static_forecast(
    result: StaticForecastResult, *, output_path: str | Path | None = None
):
    """Plot historical demand in red and future static forecasts in blue."""
    from matplotlib.figure import Figure

    history = result.data.loc[result.data["row_type"] == "historical"]
    forecast = result.data.loc[result.data["row_type"] == "forecast"]

    figure = Figure(figsize=(10, 5.5), constrained_layout=True)
    axis = figure.subplots()
    axis.plot(
        history["t"],
        history["demand"],
        color="red",
        marker="o",
        label="Historical demand",
    )
    axis.plot(
        forecast["t"],
        forecast["static_estimate"],
        color="blue",
        marker="o",
        label="Static forecast",
    )
    axis.set_title("Quarterly Demand - Static Forecast")
    axis.set_xlabel("Period")
    axis.set_ylabel("Demand")
    axis.grid(alpha=0.25)
    axis.legend()

    all_rows = result.data
    axis.set_xticks(all_rows["t"])
    axis.set_xticklabels(all_rows["period"].astype(str), rotation=45, ha="right")

    if output_path is not None:
        figure.savefig(Path(output_path), dpi=160)
    return figure
