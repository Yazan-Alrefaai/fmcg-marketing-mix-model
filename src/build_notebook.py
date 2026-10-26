"""Combine the step scripts (percent-cell format) into one executed notebook + HTML.

Usage (from the project root):
    .venv/bin/python src/build_notebook.py
"""

import json
import re
from pathlib import Path

import nbformat
import pandas as pd
from nbconvert import HTMLExporter
from nbconvert.preprocessors import ExecutePreprocessor

ROOT = Path(__file__).resolve().parents[1]
STEPS = [
    "01_load_and_clean.py",
    "02_explore_sales.py",
    "03_explore_price_promo_distribution.py",
    "04_explore_media_competitors.py",
    "05_model.py",
    "06_validate.py",
    "07_results.py",
]

INTRO = """# What drives bottled-water sales, and what is media worth?
### Marketing mix model for an FMCG bottled-water brand

**Author:** Yazan Alrefaai &nbsp;·&nbsp; **Date:** October 2026 &nbsp;·&nbsp; **Data:** 161 weeks, Jan 2022 - Jan 2025

**Question.** Help an FMCG bottled-water brand understand how effective its media is at driving sales,
and identify the other key drivers of sales.

**Contents**
1. Load and check the data
2. Sales, seasonality and weather
3. Price, promotions and distribution
4. Media and competitors
5. Model: log-linear regression with media carryover (adstock) and diminishing returns (saturation)
6. Validation: strict holdout, residual diagnostics, multicollinearity, stability, sensitivity
7. Results: decomposition, media ROI, response curves, year-on-year bridge, promotions
8. Conclusions and next steps

The model engine is in `src/mmm.py`; every modelling decision and its reason is in `docs/decision_log.md`.
"""

SETUP = """import sys
import warnings

sys.path.insert(0, "src")
warnings.filterwarnings("ignore", category=FutureWarning)"""


def split_cells(text):
    cells = []
    for block in re.split(r"^# %%", text, flags=re.M)[1:]:
        header, _, body = block.partition("\n")
        if header.strip() == "[markdown]":
            lines = [re.sub(r"^# ?", "", ln) for ln in body.strip().splitlines()]
            cells.append(nbformat.v4.new_markdown_cell("\n".join(lines)))
        elif body.strip():
            cells.append(nbformat.v4.new_code_cell(body.strip()))
    return cells


def _outputs():
    out = ROOT / "outputs"
    coef = pd.read_csv(out / "model_coefficients.csv", index_col=0)
    return {
        "media": pd.read_csv(out / "media_roi.csv", index_col=0),
        "coef": coef,
        "effect": coef["volume_effect"],
        "results": json.loads((out / "results_summary.json").read_text()),
        "holdout": pd.read_csv(out / "holdout.csv").iloc[0],
        "journey": pd.read_csv(out / "model_journey.csv"),
        "bridge": pd.read_csv(out / "volume_bridge.csv", index_col=0),
    }


def summary_markdown():
    o = _outputs()
    e, media, share = o["effect"], o["media"], o["results"]["share_of_volume"]
    final = o["journey"].iloc[-1]
    media_share = sum(share[ch] for ch in media.index)
    rows = "\n".join(
        f"| {ch} | £{r.spend / 1e3:,.0f}k | £{r.roi:.2f} | £{r.roi_low:.2f} - £{r.roi_high:.2f} | £{r.marginal_roi:.2f} |"
        for ch, r in media.sort_values("roi", ascending=False).iterrows()
    )
    b = o["bridge"]
    return f"""## Executive summary

**Model quality.** Adjusted R² {final.adj_R2:.2f}; average weekly error {final.MAPE:.1%};
error on 12 unseen weeks {o["holdout"]["holdout_MAPE"]:.1%} (whole pipeline re-run without them).

**What drives volume.** Base sales (brand, price, distribution) {share["Base"]:.0f}%, weather {share["Weather"]:.0f}%,
media {media_share:.1f}%.

| Driver | Effect on weekly volume |
|---|---|
| +1°C max temperature | {e["max_temp"]:+.1%} (and {e["hot_degrees"]:+.1%} more per °C above 20°C) |
| +10 mm rain | {e["rainfall"]:+.1%} |
| Christmas / New Year week | {e["xmas_week"]:+.0%} |
| +10% price vs competitors | {e["ln_relative_price"]:+.1%} |
| +1 point weighted distribution | {e["distribution_acv"]:+.1%} |

**Media.** All modelled media returned £{o["results"]["media_total_roi"]:.2f} of revenue per £1.

| Channel | Spend | ROI (revenue per £1) | 95% range | Next £1 returns |
|---|---|---|---|---|
{rows}

Social, Search and RDM could not be measured (wrong sign or too little spend).

**Year on year.** Volume {b.loc["Total (log pts)", "2022->2023"]:+.1f}% in 2023, mainly relative price
({b.loc["Relative price", "2022->2023"]:+.1f} pts); {b.loc["Total (log pts)", "2023->2024"]:+.1f}% in 2024, mainly distribution
({b.loc["Distribution", "2023->2024"]:+.1f} pts).

**Promotions.** About {o["results"]["promo_incremental_share"]:.0%} of promoted volume is incremental; promotions work by
widening store reach, not through discount depth.
"""


def conclusions_markdown():
    o = _outputs()
    scen = o["results"]["scenarios"]["Online partnership"]
    return f"""# 8. Conclusions and next steps

**Recommendations**
1. **Grow distribution** - the strongest controllable lever ({o["effect"]["distribution_acv"]:+.1%} volume per ACV point).
2. **Manage the price gap to competitors** - the widening premium explains most of the 2023 volume decline.
3. **Rebalance media** - moving 30% of the TV and online video budget (£{scen["moved"] / 1e3:,.0f}k) into Online
   partnership adds about £{scen["delta_revenue"] / 1e6:.1f}M revenue at the same total spend. Test OOH regionally
   before scaling it; if TV continues, spread it over more weeks.
4. **Rethink promotions** - test shallower discounts and focus on store reach.

**Limitations**
- TV ran 3 weeks and OOH 5 weeks, so their ROIs carry wide ranges; several channels overlap in time.
- ROI is revenue-based (no margin data) and short-term (no long-term brand effects).
- The price elasticity is sensitive to adding a time trend (-0.46 without, -0.10 with).
- Week-to-week correlation in residuals is handled with Newey-West robust standard errors.

**Next steps**
- Bayesian MMM (e.g. Google Meridian, PyMC-Marketing) with priors to stabilise sparse channels.
- Regional or retailer-level data, and lift tests to calibrate OOH and Online partnership.
- Margin data for profit ROI; store-level promotion evaluation.
"""


def main():
    nb = nbformat.v4.new_notebook()
    nb.cells.append(nbformat.v4.new_markdown_cell(INTRO))
    nb.cells.append(nbformat.v4.new_code_cell(SETUP))
    for step in STEPS:
        nb.cells.extend(split_cells((ROOT / "src" / step).read_text()))
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}

    ExecutePreprocessor(timeout=1200, kernel_name="python3").preprocess(nb, {"metadata": {"path": str(ROOT)}})

    # Summary and conclusions use the outputs the run just produced, so they always match
    nb.cells.insert(1, nbformat.v4.new_markdown_cell(summary_markdown()))
    nb.cells.append(nbformat.v4.new_markdown_cell(conclusions_markdown()))

    out = ROOT / "MMM_analysis.ipynb"
    nbformat.write(nb, out)
    html, _ = HTMLExporter().from_notebook_node(nb)
    (ROOT / "MMM_analysis.html").write_text(html)
    print("Wrote", out.name, "and MMM_analysis.html")


if __name__ == "__main__":
    main()
