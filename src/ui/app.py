"""Main Tkinter window for local CSV forecasting."""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from src.algorithms.forecasts import fit_static_forecast
from src.data.data_parser import (
    NEGATIVE_POLICY_NET,
    NEGATIVE_POLICY_ZERO,
    RawAggregationResult,
    aggregate_raw_quarterly_data,
    load_csv,
    select_forecast_columns,
)
from src.ui.data_table import DataFrameTable
from src.ui.state import AppState


BACKGROUND = "#bd7fa2"
PANEL_BACKGROUND = "#19dfe3"
CONTROL_BACKGROUND = "#d6e7f5"
ACTION_BACKGROUND = "#fff400"
ROW_ORDER_OPTION = "Use CSV row order (1, 2, 3, ...)"
AGGREGATED_DATA_MODE = "Already aggregated data"
RAW_DATA_MODE = "Raw transaction data"


class ForecastingApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Quarterly Demand Forecasting")
        self.geometry("1120x690")
        self.minsize(940, 570)
        self.configure(background=BACKGROUND)

        self.app_state = AppState()
        self.method_var = tk.StringVar(value="Static forecast")
        self.data_mode_var = tk.StringVar(value=AGGREGATED_DATA_MODE)
        self.negative_policy_var = tk.StringVar(value=NEGATIVE_POLICY_NET)
        self.periodicity_var = tk.StringVar(value="4")
        self.horizon_var = tk.StringVar(value="4")
        self.period_column_var = tk.StringVar()
        self.demand_column_var = tk.StringVar()
        self.source_label_var = tk.StringVar(value="No CSV selected")
        self.output_label_var = tk.StringVar(value="No output CSV selected")
        self.plot_label_var = tk.StringVar(value="No plot file selected")
        self.status_var = tk.StringVar(value="Select a CSV file to begin.")

        self._configure_styles()
        self._build_layout()

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure("App.TFrame", background=BACKGROUND)
        style.configure("Controls.TFrame", background=BACKGROUND)
        style.configure("DataPanel.TFrame", background=PANEL_BACKGROUND)
        style.configure(
            "Control.TButton",
            background=CONTROL_BACKGROUND,
            foreground="#101820",
            font=("TkDefaultFont", 12),
            padding=(10, 8),
        )
        style.map("Control.TButton", background=[("active", "#ebf4fb")])
        style.configure(
            "Control.TLabel",
            background=BACKGROUND,
            foreground="#101820",
            font=("TkDefaultFont", 11),
        )
        style.configure(
            "Path.TLabel",
            background=BACKGROUND,
            foreground="#342330",
            font=("TkDefaultFont", 9),
        )
        style.configure(
            "PanelStatus.TLabel",
            background=PANEL_BACKGROUND,
            foreground="#102025",
        )
        style.configure(
            "Forecast.Treeview",
            background=PANEL_BACKGROUND,
            fieldbackground=PANEL_BACKGROUND,
            foreground="#102025",
            rowheight=25,
        )
        style.configure(
            "Forecast.Treeview.Heading",
            background="#d6e7f5",
            foreground="#101820",
            font=("TkDefaultFont", 10, "bold"),
        )

    def _build_layout(self) -> None:
        container = ttk.Frame(self, padding=16, style="App.TFrame")
        container.pack(fill="both", expand=True)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(0, weight=1)

        controls = ttk.Frame(container, padding=(0, 0, 18, 0), style="Controls.TFrame")
        controls.grid(row=0, column=0, sticky="nsw")
        results = ttk.Frame(container, style="App.TFrame")
        results.grid(row=0, column=1, sticky="nsew")
        results.columnconfigure(0, weight=1)
        results.rowconfigure(0, weight=1)

        self._build_controls(controls)
        self._build_results(results)

    def _build_controls(self, parent: ttk.Frame) -> None:
        file_row = ttk.Frame(parent, style="Controls.TFrame")
        file_row.pack(fill="x", pady=(0, 4))
        ttk.Button(
            file_row,
            text="Select file",
            command=self.select_file,
            style="Control.TButton",
            width=20,
        ).pack(side="left")
        ttk.Button(
            file_row,
            text="GO",
            command=self.load_selected_file,
            style="Control.TButton",
            width=5,
        ).pack(side="left", padx=(8, 0))
        ttk.Label(
            parent,
            textvariable=self.source_label_var,
            style="Path.TLabel",
            wraplength=290,
        ).pack(fill="x", pady=(0, 14))

        self._labeled_combobox(
            parent,
            "Select method",
            self.method_var,
            values=("Static forecast",),
        )

        data_mode_box = self._labeled_combobox(
            parent,
            "Select data structure",
            self.data_mode_var,
            values=(AGGREGATED_DATA_MODE, RAW_DATA_MODE),
        )
        data_mode_box.bind("<<ComboboxSelected>>", self._on_data_mode_changed)

        self.raw_options_container = ttk.Frame(parent, style="Controls.TFrame")
        self.raw_options_container.pack(fill="x")
        self.raw_options_content = ttk.Frame(
            self.raw_options_container,
            style="Controls.TFrame",
        )
        ttk.Label(
            self.raw_options_content,
            text="Negative transaction handling",
            style="Control.TLabel",
        ).pack(anchor="w")
        ttk.Radiobutton(
            self.raw_options_content,
            text="Net quarterly totals (recommended)",
            variable=self.negative_policy_var,
            value=NEGATIVE_POLICY_NET,
        ).pack(anchor="w", pady=(3, 0))
        ttk.Radiobutton(
            self.raw_options_content,
            text="Set negatives to zero (gross totals; confirmation required)",
            variable=self.negative_policy_var,
            value=NEGATIVE_POLICY_ZERO,
        ).pack(anchor="w")

        ttk.Label(parent, text="Select periodicity", style="Control.TLabel").pack(
            anchor="w"
        )
        ttk.Spinbox(
            parent,
            from_=2,
            to=24,
            textvariable=self.periodicity_var,
            width=27,
        ).pack(fill="x", pady=(3, 13))

        ttk.Label(parent, text="Select horizon", style="Control.TLabel").pack(
            anchor="w"
        )
        ttk.Spinbox(
            parent,
            from_=1,
            to=40,
            textvariable=self.horizon_var,
            width=27,
        ).pack(fill="x", pady=(3, 13))

        ttk.Button(
            parent,
            text="Select optional output CSV path",
            command=self.select_output_csv,
            style="Control.TButton",
        ).pack(fill="x")
        ttk.Label(
            parent,
            textvariable=self.output_label_var,
            style="Path.TLabel",
            wraplength=290,
        ).pack(fill="x", pady=(3, 13))

        ttk.Button(
            parent,
            text="Select optional plot file for graph",
            command=self.select_plot_file,
            style="Control.TButton",
        ).pack(fill="x")
        ttk.Label(
            parent,
            textvariable=self.plot_label_var,
            style="Path.TLabel",
            wraplength=290,
        ).pack(fill="x", pady=(3, 22))

        run_button = tk.Button(
            parent,
            text="Run forecast",
            command=self.run_forecast,
            background=ACTION_BACKGROUND,
            activebackground="#fff975",
            foreground="#111111",
            font=("TkDefaultFont", 14, "bold"),
            relief="raised",
            padx=20,
            pady=20,
        )
        run_button.pack(fill="x", padx=28)

        ttk.Label(
            parent,
            textvariable=self.status_var,
            style="Control.TLabel",
            wraplength=300,
            justify="left",
        ).pack(fill="x", pady=(22, 0))

    def _build_results(self, parent: ttk.Frame) -> None:
        self.table = DataFrameTable(parent)
        self.table.grid(row=0, column=0, sticky="nsew")

        selectors = ttk.Frame(parent, padding=(0, 10, 0, 0), style="App.TFrame")
        selectors.grid(row=1, column=0, sticky="ew")
        selectors.columnconfigure(0, weight=1)
        selectors.columnconfigure(1, weight=1)

        period_frame = ttk.Frame(selectors, style="Controls.TFrame")
        period_frame.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        demand_frame = ttk.Frame(selectors, style="Controls.TFrame")
        demand_frame.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        self.period_column_label = ttk.Label(
            period_frame,
            text="Period column (optional)",
            style="Control.TLabel",
        )
        self.period_column_label.pack(anchor="w")
        self.period_column_box = ttk.Combobox(
            period_frame,
            textvariable=self.period_column_var,
            state="disabled",
        )
        self.period_column_box.pack(fill="x", pady=(3, 0))

        self.demand_column_label = ttk.Label(
            demand_frame,
            text="Select demand column",
            style="Control.TLabel",
        )
        self.demand_column_label.pack(anchor="w")
        self.demand_column_box = ttk.Combobox(
            demand_frame,
            textvariable=self.demand_column_var,
            state="disabled",
        )
        self.demand_column_box.pack(fill="x", pady=(3, 0))

    def _labeled_combobox(
        self,
        parent: ttk.Frame,
        label: str,
        variable: tk.StringVar,
        *,
        values: tuple[str, ...],
    ) -> ttk.Combobox:
        ttk.Label(parent, text=label, style="Control.TLabel").pack(anchor="w")
        box = ttk.Combobox(
            parent,
            textvariable=variable,
            values=values,
            state="readonly",
        )
        box.pack(fill="x", pady=(3, 13))
        return box

    def select_file(self) -> None:
        selected = filedialog.askopenfilename(
            parent=self,
            title="Select demand CSV",
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*")),
        )
        if not selected:
            return
        self.app_state.source_path = Path(selected)
        self.source_label_var.set(str(self.app_state.source_path))
        self.load_selected_file()

    def load_selected_file(self) -> None:
        path = self.app_state.source_path
        if path is None:
            self._show_error("Select a CSV file before pressing GO.")
            return
        if not path.is_file():
            self.app_state.clear_loaded_data()
            self._disable_column_selectors()
            self._show_error(f"The selected CSV does not exist:\n{path}")
            return

        self._set_busy(True, "Loading CSV...")
        try:
            data = load_csv(path)
            self.app_state.set_loaded_data(data)
            self.table.show_dataframe(data)
            self._configure_column_selectors(list(data.columns))
            self.status_var.set(
                f"Loaded {len(data):,} rows and {len(data.columns):,} columns."
            )
        except Exception as exc:
            self.app_state.clear_loaded_data()
            self._disable_column_selectors()
            self._show_error(f"Unable to load the selected CSV:\n{exc}")
        finally:
            self._set_busy(False)

    def select_output_csv(self) -> None:
        selected = filedialog.asksaveasfilename(
            parent=self,
            title="Save forecast DataFrame",
            initialfile="forecast_csv",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if selected:
            self.app_state.output_csv_path = Path(selected)
            self.output_label_var.set(str(self.app_state.output_csv_path))

    def select_plot_file(self) -> None:
        selected = filedialog.asksaveasfilename(
            parent=self,
            title="Save forecast chart",
            initialfile="forecast_graph",
            defaultextension=".png",
            filetypes=[("PNG image", "*.png")]
        )
        if selected:
            self.app_state.plot_path = Path(selected)
            self.plot_label_var.set(str(self.app_state.plot_path))

    def run_forecast(self) -> None:
        if self.app_state.raw_data is None:
            self._show_error("Load a CSV file before running a forecast.")
            return
        if self.method_var.get() != "Static forecast":
            self._show_error("The selected forecasting method is not available yet.")
            return

        first_column = self.period_column_var.get().strip()
        second_column = self.demand_column_var.get().strip()
        raw_mode = self.data_mode_var.get() == RAW_DATA_MODE
        if raw_mode and not first_column:
            self._show_error("Select a transaction date column.")
            return
        if not second_column:
            label = "transaction amount" if raw_mode else "demand"
            self._show_error(f"Select a {label} column.")
            return

        try:
            periodicity = int(self.periodicity_var.get())
            horizon = int(self.horizon_var.get())
        except ValueError:
            self._show_error("Periodicity and horizon must be whole numbers.")
            return

        self._set_busy(True, "Calculating static forecast...")
        try:
            aggregation: RawAggregationResult | None = None
            if raw_mode:
                aggregation = aggregate_raw_quarterly_data(
                    self.app_state.raw_data,
                    date_column=first_column,
                    amount_column=second_column,
                    negative_policy=self.negative_policy_var.get(),
                )
                if (
                    aggregation.negative_policy == NEGATIVE_POLICY_ZERO
                    and aggregation.negative_count
                ):
                    confirmed = messagebox.askyesno(
                        "Confirm negative-value conversion",
                        (
                            f"The source contains {aggregation.negative_count:,} "
                            "negative transactions totaling "
                            f"${abs(aggregation.negative_total):,.2f}.\n\n"
                            "Setting these values to zero excludes refunds and "
                            "cancellations before quarterly aggregation. The forecast "
                            "will represent gross demand and may overforecast net "
                            "demand. Net quarterly aggregation is recommended.\n\n"
                            "Continue with the zero-conversion override?"
                        ),
                        icon="warning",
                        parent=self,
                    )
                    if not confirmed:
                        self.status_var.set(
                            "Forecast cancelled; negative transactions were not changed."
                        )
                        return
                selected_data = aggregation.data
            else:
                period_column = (
                    None
                    if not first_column or first_column == ROW_ORDER_OPTION
                    else first_column
                )
                selected_data = select_forecast_columns(
                    self.app_state.raw_data,
                    period_column=period_column,
                    demand_column=second_column,
                )
            result = fit_static_forecast(
                selected_data,
                periodicity=periodicity,
                horizon=horizon,
            )
            self.app_state.forecast_result = result
            self.table.show_dataframe(result.data)

            saved_items: list[str] = []
            if self.app_state.output_csv_path is not None:
                self.app_state.output_csv_path.parent.mkdir(parents=True, exist_ok=True)
                result.data.to_csv(self.app_state.output_csv_path, index=False)
                saved_items.append(f"CSV: {self.app_state.output_csv_path}")

            from src.data.plotting import plot_static_forecast
            from src.ui.chart_window import ForecastChartWindow

            if self.app_state.plot_path is not None:
                self.app_state.plot_path.parent.mkdir(parents=True, exist_ok=True)
                saved_items.append(f"Plot: {self.app_state.plot_path}")
            figure = plot_static_forecast(
                result,
                output_path=self.app_state.plot_path,
            )
            ForecastChartWindow(self, figure)

            factors = ", ".join(
                f"S{season}={factor:.4f}"
                for season, factor in result.seasonal_factors.items()
            )
            status = (
                f"Forecast complete. Level={result.level:,.2f}; "
                f"trend={result.trend:,.2f}. {factors}"
            )
            if aggregation is not None:
                aggregation_status = (
                    f"Aggregated {aggregation.transaction_count:,} transactions into "
                    f"{len(aggregation.data):,} calendar quarters."
                )
                if aggregation.negative_count:
                    if aggregation.negative_policy == NEGATIVE_POLICY_NET:
                        aggregation_status += (
                            f" Included {aggregation.negative_count:,} negative "
                            "transactions totaling "
                            f"-${abs(aggregation.negative_total):,.2f} in net totals."
                        )
                    else:
                        aggregation_status += (
                            f" Converted {aggregation.negative_count:,} negative "
                            "transactions totaling "
                            f"-${abs(aggregation.negative_total):,.2f} to zero; these "
                            "are gross totals."
                        )
                if aggregation.missing_quarters_filled:
                    aggregation_status += (
                        f" Filled {aggregation.missing_quarters_filled:,} missing "
                        "quarters with zero demand."
                    )
                status = aggregation_status + "\n" + status
            if saved_items:
                status += "\n" + "\n".join(saved_items)
            self.status_var.set(status)
        except Exception as exc:
            self._show_error(f"Forecast failed:\n{exc}")
        finally:
            self._set_busy(False)

    def _configure_column_selectors(self, columns: list[object]) -> None:
        column_names = [str(column) for column in columns]
        if self.data_mode_var.get() == RAW_DATA_MODE:
            self.period_column_box.configure(values=column_names, state="readonly")
            self.period_column_var.set(
                self._suggest_column(column_names, ("date", "time", "period"))
            )
            demand_keywords = (
                "amount",
                "amt",
                "demand",
                "sales",
                "volume",
                "value",
            )
        else:
            self.period_column_box.configure(
                values=[ROW_ORDER_OPTION, *column_names],
                state="readonly",
            )
            self.period_column_var.set(ROW_ORDER_OPTION)
            demand_keywords = ("demand", "sales", "volume", "value", "amount", "amt")
        self.demand_column_box.configure(values=column_names, state="readonly")
        self.demand_column_var.set(
            self._suggest_column(column_names, demand_keywords)
        )

    def _on_data_mode_changed(self, _event: object | None = None) -> None:
        if self.data_mode_var.get() == RAW_DATA_MODE:
            self.raw_options_content.pack(fill="x", pady=(0, 13))
            self.period_column_label.configure(text="Transaction date column")
            self.demand_column_label.configure(text="Transaction amount column")
        else:
            self.raw_options_content.pack_forget()
            self.period_column_label.configure(text="Period column (optional)")
            self.demand_column_label.configure(text="Select demand column")

        if self.app_state.raw_data is not None:
            self._configure_column_selectors(list(self.app_state.raw_data.columns))

    def _disable_column_selectors(self) -> None:
        self.period_column_var.set("")
        self.demand_column_var.set("")
        self.period_column_box.configure(values=(), state="disabled")
        self.demand_column_box.configure(values=(), state="disabled")

    @staticmethod
    def _suggest_column(columns: list[str], keywords: tuple[str, ...]) -> str:
        for keyword in keywords:
            for column in columns:
                if keyword in column.casefold():
                    return column
        return columns[0] if columns else ""

    def _show_error(self, message: str) -> None:
        self.table.show_message(message, is_error=True)
        self.status_var.set(message.replace("\n", " "))
        messagebox.showerror("Forecasting error", message, parent=self)

    def _set_busy(self, busy: bool, status: str | None = None) -> None:
        self.configure(cursor="watch" if busy else "")
        if status is not None:
            self.status_var.set(status)
        self.update_idletasks()


def run_gui() -> None:
    app = ForecastingApp()
    app.mainloop()
