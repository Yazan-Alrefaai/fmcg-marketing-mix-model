"""Shared chart style so every chart in the project looks the same."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CHARTS = ROOT / "outputs" / "charts"
CHARTS.mkdir(parents=True, exist_ok=True)

# Categorical colours, always used in this order
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
SURFACE = "#fcfcfb"

plt.rcParams.update(
    {
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "font.family": "sans-serif",
        "font.size": 10,
        "text.color": INK,
        "axes.edgecolor": AXIS,
        "axes.labelcolor": INK_2,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": GRID,
        "grid.linewidth": 0.6,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "lines.linewidth": 2,
        "legend.frameon": False,
    }
)


def load():
    df = pd.read_csv(ROOT / "data" / "clean.csv", parse_dates=["Date"])
    return df


def save(fig, name):
    path = CHARTS / f"{name}.png"
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    try:  # show the chart inline when running inside Jupyter
        from IPython import get_ipython
        from IPython.display import Image, display

        if get_ipython() is not None:
            display(Image(str(path)))
            return
    except ImportError:
        pass
    print("Chart saved:", path.name)


def thousands(ax, axis="y"):
    fmt = plt.FuncFormatter(lambda v, _: f"{v / 1e6:.1f}M" if abs(v) >= 1e6 else f"{v / 1e3:.0f}k")
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(fmt)
