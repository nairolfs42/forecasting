from __future__ import annotations

from pathlib import Path
import pandas as pd


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


def select_forecast_columns(data: pd.DataFrame,*,period_column: str,demand_column: str,) -> pd.DataFrame:
    """Select, validate, and normalize the chosen columns."""
    missing = [
        column
        for column in (period_column, demand_column)
        if column not in data.columns
    ]
    if missing:
        raise ValueError(f"selected columns not found: {missing}")
    if period_column == demand_column:
        raise ValueError("period and demand must use different columns")

    selected = data[[period_column, demand_column]].copy()
    selected.columns = ["period", "demand"]
    if selected["period"].isna().any():
        raise ValueError("period column contains missing values")
    if selected["period"].duplicated().any():
        duplicates = selected.loc[selected["period"].duplicated(), "period"].tolist()
        raise ValueError(f"period column contains duplicates: {duplicates[:5]}")

    selected["demand"] = _parse_numeric(selected["demand"], raise_on_invalid=True)
    if selected["demand"].isna().any():
        raise ValueError("demand column contains missing values")
    if (selected["demand"] < 0).any():
        raise ValueError("demand values must be non-negative for this proof of concept")

    numeric_periods = pd.to_numeric(selected["period"], errors="coerce")
    if numeric_periods.notna().all():
        selected["period"] = numeric_periods

    selected = selected.sort_values("period", kind="stable").reset_index(drop=True)
    return selected


def _parse_numeric(series: pd.Series, *, raise_on_invalid: bool) -> pd.Series:
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
        raise ValueError(f"demand column contains non-numeric values: {examples}")
    return parsed
