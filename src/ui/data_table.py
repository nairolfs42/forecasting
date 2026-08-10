"""Scrollable DataFrame presentation helpers for Tkinter."""

from __future__ import annotations

import math
import tkinter as tk
from tkinter import ttk

import pandas as pd


def prepare_dataframe_preview(
    data: pd.DataFrame, *, max_rows: int = 400
) -> tuple[pd.DataFrame, str]:
    """Return a bounded preview while retaining both the start and end rows."""
    if max_rows < 2:
        raise ValueError("max_rows must be at least 2")
    if len(data) <= max_rows:
        return data.copy(), f"Showing all {len(data):,} rows"

    leading_rows = math.ceil(max_rows / 2)
    trailing_rows = max_rows - leading_rows
    preview = pd.concat(
        [data.head(leading_rows), data.tail(trailing_rows)],
        ignore_index=True,
    )
    return preview, f"Showing {max_rows:,} of {len(data):,} rows (first and last rows)"


def format_table_value(value: object) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:,.4f}".rstrip("0").rstrip(".")
    return str(value)


class DataFrameTable(ttk.Frame):
    """Treeview wrapper that displays DataFrames or an in-panel message."""

    def __init__(self, master: tk.Misc, *, max_rows: int = 400) -> None:
        super().__init__(master, style="DataPanel.TFrame")
        self.max_rows = max_rows

        self.tree = ttk.Treeview(self, show="headings", style="Forecast.Treeview")
        vertical = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        horizontal = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(
            yscrollcommand=vertical.set,
            xscrollcommand=horizontal.set,
        )

        self.tree.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        self.row_summary = ttk.Label(
            self,
            text="No CSV loaded",
            anchor="w",
            style="PanelStatus.TLabel",
        )
        self.row_summary.grid(row=2, column=0, columnspan=2, sticky="ew", padx=6, pady=4)

        self.message = tk.Label(
            self,
            text="Select a CSV file to preview its data.",
            background="#19dfe3",
            foreground="#102025",
            font=("TkDefaultFont", 15),
            justify="center",
            wraplength=560,
        )
        self.message.place(relx=0.5, rely=0.46, anchor="center")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

    def show_message(self, text: str, *, is_error: bool = False) -> None:
        self._clear_tree()
        self.message.configure(
            text=text,
            foreground="#8b1020" if is_error else "#102025",
        )
        self.message.place(relx=0.5, rely=0.46, anchor="center")
        self.row_summary.configure(text="Error" if is_error else "No data")

    def show_dataframe(self, data: pd.DataFrame) -> None:
        self._clear_tree()
        self.message.place_forget()
        preview, summary = prepare_dataframe_preview(data, max_rows=self.max_rows)

        columns = [str(column) for column in preview.columns]
        self.tree.configure(columns=columns)
        for column in columns:
            self.tree.heading(column, text=column)
            self.tree.column(column, width=135, minwidth=90, anchor="center")

        for row in preview.itertuples(index=False, name=None):
            self.tree.insert(
                "",
                "end",
                values=[format_table_value(value) for value in row],
            )
        self.row_summary.configure(text=summary)

    def _clear_tree(self) -> None:
        children = self.tree.get_children()
        if children:
            self.tree.delete(*children)
        self.tree.configure(columns=())
