from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


NEGATIVE_POLICY_NET = "net"
NEGATIVE_POLICY_ZERO = "zero"


@dataclass(frozen=True)
class RawAggregationResult:
    """Quarterly data plus details about raw-transaction normalization."""

    data: pd.DataFrame
    transaction_count: int
    negative_count: int
    negative_total: float
    missing_quarters_filled: int
    negative_policy: str


def load_csv(path: str | Path) -> pd.DataFrame:
    """Load a non-empty CSV and trim surrounding whitespace from headers."""
    csv_path = Path(path).expanduser()

    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    data = pd.read_csv(csv_path)
    if data.empty:
        raise ValueError(f"CSV contains no data rows: {csv_path}")

    data.columns = [str(column).strip() for column in data.columns]
    if data.columns.duplicated().any():
        duplicates = data.columns[data.columns.duplicated()].tolist()
        raise ValueError(f"CSV has duplicate column names: {duplicates}")
    return data


def profile_columns(data: pd.DataFrame) -> pd.DataFrame:
    """Summarize columns to support period and demand selection."""
    profiles: list[dict[str, object]] = []
    for column in data.columns:
        values = data[column]
        parsed_numeric = _parse_numeric(values, raise_on_invalid=False)
        non_null_count = int(values.notna().sum())
        numeric_count = int(parsed_numeric.notna().sum())
        samples = values.dropna().astype(str).head(3).tolist()
        profiles.append(
            {
                "column": column,
                "dtype": str(values.dtype),
                "non_null": non_null_count,
                "missing": int(values.isna().sum()),
                "unique": int(values.nunique(dropna=True)),
                "numeric_percent": (
                    round(100.0 * numeric_count / non_null_count, 1)
                    if non_null_count
                    else 0.0
                ),
                "sample": " | ".join(samples),
            }
        )
    return pd.DataFrame(profiles)


def select_forecast_columns(
    data: pd.DataFrame,
    *,
    period_column: str | None = None,
    demand_column: str,
) -> pd.DataFrame:
    """Select and normalize forecasting columns.

    When ``period_column`` is omitted, CSV row order is treated as chronological
    order and one-based periods are generated as ``1..n``.
    """
    requested_columns = [demand_column]
    if period_column:
        requested_columns.append(period_column)
    missing = [column for column in requested_columns if column not in data.columns]
    if missing:
        raise ValueError(f"selected columns not found: {missing}")
    if period_column and period_column == demand_column:
        raise ValueError("period and demand must use different columns")

    if period_column:
        selected = data[[period_column, demand_column]].copy()
        selected.columns = ["period", "demand"]
        if selected["period"].isna().any():
            raise ValueError("period column contains missing values")
        if selected["period"].duplicated().any():
            duplicates = selected.loc[
                selected["period"].duplicated(), "period"
            ].tolist()
            raise ValueError(f"period column contains duplicates: {duplicates[:5]}")

        numeric_periods = pd.to_numeric(selected["period"], errors="coerce")
        if numeric_periods.notna().all():
            selected["period"] = numeric_periods
        selected = selected.sort_values("period", kind="stable").reset_index(drop=True)
    else:
        selected = pd.DataFrame(
            {
                "period": range(1, len(data) + 1),
                "demand": data[demand_column].to_numpy(copy=True),
            }
        )

    selected["demand"] = _parse_numeric(selected["demand"], raise_on_invalid=True)
    if selected["demand"].isna().any():
        raise ValueError("demand column contains missing values")
    if (selected["demand"] < 0).any():
        raise ValueError("demand values must be non-negative for this version of the static forecast")

    return selected


def aggregate_raw_quarterly_data(
    data: pd.DataFrame,
    *,
    date_column: str,
    amount_column: str,
    negative_policy: str = NEGATIVE_POLICY_NET,
) -> RawAggregationResult:
    """Normalize raw transactions and aggregate them into calendar quarters.

    Net aggregation keeps negative refunds and cancellations in their quarter.
    The zero policy is an explicit gross-demand override that removes negative
    transactions before aggregation.
    """
    requested_columns = [date_column, amount_column]
    missing = [column for column in requested_columns if column not in data.columns]
    if missing:
        raise ValueError(f"selected raw-data columns not found: {missing}")
    if date_column == amount_column:
        raise ValueError("transaction date and amount must use different columns")
    if negative_policy not in {NEGATIVE_POLICY_NET, NEGATIVE_POLICY_ZERO}:
        raise ValueError(f"unknown negative-value policy: {negative_policy}")

    source_dates = data[date_column]
    dates = pd.to_datetime(source_dates, errors="coerce", format="mixed")
    invalid_dates = source_dates.notna() & dates.isna()
    if invalid_dates.any():
        examples = source_dates.loc[invalid_dates].astype(str).head(5).tolist()
        raise ValueError(
            f"transaction date column contains invalid dates: {examples}"
        )
    if dates.isna().any():
        raise ValueError("transaction date column contains missing values")

    amounts = _parse_numeric(
        data[amount_column],
        raise_on_invalid=True,
        field_name="transaction amount",
    )
    if amounts.isna().any():
        raise ValueError("transaction amount column contains missing values")

    negative_mask = amounts < 0
    negative_count = int(negative_mask.sum())
    negative_total = float(amounts.loc[negative_mask].sum())
    amounts_for_aggregation = amounts
    if negative_policy == NEGATIVE_POLICY_ZERO:
        amounts_for_aggregation = amounts.clip(lower=0.0)

    transaction_quarters = dates.dt.to_period("Q")
    quarterly_totals = amounts_for_aggregation.groupby(
        transaction_quarters, sort=True
    ).sum()
    first_quarter = transaction_quarters.min()
    last_quarter = transaction_quarters.max()
    all_quarters = pd.period_range(first_quarter, last_quarter, freq="Q")
    missing_quarters_filled = int(len(all_quarters.difference(quarterly_totals.index)))
    quarterly_totals = quarterly_totals.reindex(all_quarters, fill_value=0.0)

    if negative_policy == NEGATIVE_POLICY_NET and (quarterly_totals < 0).any():
        negative_quarters = [
            str(period) for period in quarterly_totals.index[quarterly_totals < 0]
        ]
        raise ValueError(
            "net aggregation produced negative quarterly demand for "
            f"{negative_quarters[:5]}. Review those transactions or use the "
            "acknowledged zero-conversion override."
        )

    quarterly_data = pd.DataFrame(
        {
            "period": all_quarters,
            "demand": quarterly_totals.to_numpy(dtype=float),
        }
    )
    return RawAggregationResult(
        data=quarterly_data,
        transaction_count=len(data),
        negative_count=negative_count,
        negative_total=negative_total,
        missing_quarters_filled=missing_quarters_filled,
        negative_policy=negative_policy,
    )


def _parse_numeric(
    series: pd.Series,
    *,
    raise_on_invalid: bool,
    field_name: str = "demand",
) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce").astype(float)

    text = series.astype("string").str.strip()
    text = text.str.replace(",", "", regex=False)
    text = text.str.replace("$", "", regex=False)
    text = text.str.replace("£", "", regex=False)
    text = text.str.replace("€", "", regex=False)
    text = text.str.replace(r"^\((.*)\)$", r"-\1", regex=True)
    parsed = pd.to_numeric(text, errors="coerce").astype(float)

    invalid = series.notna() & parsed.isna()
    if raise_on_invalid and invalid.any():
        examples = series.loc[invalid].astype(str).head(5).tolist()
        raise ValueError(f"{field_name} column contains non-numeric values: {examples}")
    return parsed
