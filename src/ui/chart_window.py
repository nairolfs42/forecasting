"""Interactive Matplotlib chart window for forecast results."""

from __future__ import annotations

import tkinter as tk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


class ForecastChartWindow(tk.Toplevel):
    """Display a Matplotlib figure in a separate Tkinter window."""

    def __init__(self, parent: tk.Misc, figure: Figure) -> None:
        super().__init__(parent)
        self.figure = figure

        self.title("Forecast chart")
        self.geometry("1000x650")
        self.minsize(720, 480)

        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.draw()

        self.toolbar = NavigationToolbar2Tk(
            self.canvas,
            self,
            pack_toolbar=False,
        )
        self.toolbar.update()
        self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.protocol("WM_DELETE_WINDOW", self._close)
        self.lift()
        self.focus_set()

    def _close(self) -> None:
        self.figure.clear()
        self.destroy()
