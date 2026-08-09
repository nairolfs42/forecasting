from __future__ import annotations

import argparse
from pathlib import Path

from src.algorithms.forecasts import fit_static_forecast
from src.data.data_parser import load_csv, profile_columns, select_forecast_columns


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect a CSV."
        )
    )
    parser.add_argument("csv_path", type=Path, help="Path to the source CSV file")
    parser.add_argument("--period-column", help="Column containing ordered periods")
    parser.add_argument("--demand-column", help="Column containing demand values")
    parser.add_argument(
        "--periodicity",
        type=int,
        default=4,
        help="Number of periods in one seasonal cycle (default: 4 quarters)",
    )
    parser.add_argument(
        "--horizon",
        type=int,
        default=4,
        help="Number of future periods to forecast (default: 4 quarters)",
    )
    parser.add_argument("--output", type=Path, help="Optional output CSV path")
    parser.add_argument(
        "--plot",
        type=Path,
        help="Optional PNG path for a red historical / blue forecast chart",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    raw_data = load_csv(args.csv_path)

    print("\nAvailable columns")
    print(profile_columns(raw_data).to_string(index=False))

    if not args.period_column or not args.demand_column:
        print(
            "\nChoose columns and rerun with --period-column [column name] and --demand-column [column name]."
        )
        return 0

    selected_data = select_forecast_columns(
        raw_data,
        period_column=args.period_column,
        demand_column=args.demand_column,
    )
    result = fit_static_forecast(
        selected_data,
        periodicity=args.periodicity,
        horizon=args.horizon,
    )

    print(f"\nLevel at t=0: {result.level:,.6f}")
    print(f"Trend per period: {result.trend:,.6f}")
    print("Seasonal factors")
    print(result.seasonal_factors.to_string())
    print("\nStatic forecast output")
    print(result.data.to_string(index=False))

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        result.data.to_csv(args.output, index=False)
        print(f"\nSaved data to {args.output}")

    if args.plot:
        from src.data.plotting import plot_static_forecast

        args.plot.parent.mkdir(parents=True, exist_ok=True)
        plot_static_forecast(result, output_path=args.plot)
        print(f"Saved chart to {args.plot}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
