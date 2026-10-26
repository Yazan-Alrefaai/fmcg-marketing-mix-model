"""Export every number the presentation needs to deck/deck_data.json,
so the slides always match the model outputs."""

import json

import numpy as np
import pandas as pd

import mmm
from style import ROOT, load

df = load()
OUT = ROOT / "outputs"
rates = json.loads((OUT / "model_config.json").read_text())["rates"]
model = mmm.MMM(df, rates)
b, res = model.params, model.res
price = df["Avg_PPKG"].to_numpy()
spend = model.actual_spend()

media = pd.read_csv(OUT / "media_roi.csv", index_col=0)
bridge = pd.read_csv(OUT / "volume_bridge.csv", index_col=0)
journey = pd.read_csv(OUT / "model_journey.csv")
holdout = pd.read_csv(OUT / "holdout.csv").iloc[0]
summary = json.loads((OUT / "results_summary.json").read_text())
parts = model.decompose()

# Monthly view keeps the decomposition chart readable (average week per month)
monthly = parts.copy()
monthly["Base"] = monthly["Base"] + monthly["Christmas week"]
monthly["Media"] = monthly[model.channels].sum(axis=1)
monthly = monthly[["Base", "Weather", "Media"]].resample("MS").mean()  # months have 4 or 5 weeks
monthly = monthly.iloc[:-1]  # drop partial January 2025

weekly = pd.DataFrame(
    {
        "date": df["Date"].dt.strftime("%b %y"),
        "volume": df["Volume_Sales"] / 1e6,
        "temp": df["weather_max_temp"],
    }
)

# Response curves on one shared spend grid (needed for a native chart)
grid = np.arange(0, 1_600_001, 100_000)
curves = {}
for ch in model.channels:
    total = spend[ch].sum()
    vals = []
    for g in grid:
        s = {**spend, ch: spend[ch] * (g / total)}
        vals.append(float((model.channel_incremental(ch, spend=s) * price).sum() / 1e6))
    curves[ch] = vals

yr = df["Date"].dt.year
year_avg = (
    df.assign(year=yr)
    .groupby("year")
    .agg(
        base_price=("Base_Avg_PPKG", "mean"),
        volume=("Volume_Sales", "mean"),
        promo_share=("Promotion_Volume_Sales", "sum"),
        vol_total=("Volume_Sales", "sum"),
        acv=("ACV_Weighted_Distribution_wtd", "mean"),
    )
)
year_avg["promo_share"] = year_avg["promo_share"] / year_avg["vol_total"]
rel = np.exp(model.X["ln_relative_price"]).groupby(yr).mean()
depth = (
    (1 - df["Promotion_Avg_PPKG"] / df["Base_Avg_PPKG"])
    .where(df["Promotion_Volume_Sales"] / df["Volume_Sales"] >= 0.05)
    .groupby(yr)
    .mean()
)

media_cols = [c for c in df.columns if c.startswith("Media_") and c.endswith("_Spends")]
data = {
    "facts": {
        "weeks": len(df),
        "variables": df.shape[1],
        "start": df["Date"].min().strftime("%b %Y"),
        "end": df["Date"].max().strftime("%b %Y"),
        "value_sales_m": float(df["Value_Sales"].sum() / 1e6),
        "media_spend_m": float(df[media_cols].sum().sum() / 1e6),
        "media_pct_sales": float(df[media_cols].sum().sum() / df["Value_Sales"].sum()),
        "temp_corr": float(df["Volume_Sales"].corr(df["weather_max_temp"])),
    },
    "weekly": weekly.to_dict(orient="list"),
    "monthly": {
        "labels": [d.strftime("%b %y") for d in monthly.index],
        **{k: (monthly[k] / 1e6).round(3).tolist() for k in monthly.columns},
    },
    "share": summary["share_of_volume"],
    "media": media.reset_index().to_dict(orient="records"),
    "media_total_roi": summary["media_total_roi"],
    "not_measured": {ch: float(mmm.channel_spend(df, ch).sum()) for ch in ["Social", "Search", "RDM"]},
    "curves": {"grid_k": (grid / 1e3).astype(int).tolist(), **curves},
    "actual_spend_k": {ch: float(spend[ch].sum() / 1e3) for ch in model.channels},
    "scenarios": summary["scenarios"],
    "bridge": {
        "drivers": bridge.index.drop("Total (log pts)").tolist(),
        **{col: bridge[col].drop("Total (log pts)").round(1).tolist() for col in bridge.columns},
        "totals": bridge.loc["Total (log pts)"].round(1).to_dict(),
    },
    "effects": {
        "temp": float(np.exp(b["max_temp"]) - 1),
        "hot": float(np.exp(b["hot_degrees"]) - 1),
        "rain10": float(np.exp(10 * b["rainfall"]) - 1),
        "xmas": float(np.exp(b["xmas_week"]) - 1),
        "price10": float(1.1 ** b["ln_relative_price"] - 1),
        "elasticity": float(b["ln_relative_price"]),
        "acv1": float(np.exp(b["distribution_acv"]) - 1),
        "acv1_revenue_m": float(
            (np.exp(b["distribution_acv"]) - 1) * df.loc[yr == 2024, "Value_Sales"].sum() / 1e6
        ),
    },
    "years": {
        "base_price": year_avg["base_price"].round(3).to_dict(),
        "relative_price": rel.round(3).to_dict(),
        "acv": year_avg["acv"].round(1).to_dict(),
        "promo_share": year_avg["promo_share"].round(3).to_dict(),
        "promo_depth": depth.round(3).to_dict(),
    },
    "promo": {
        "lift": summary["promo_lift_via_distribution"],
        "incremental_share": summary["promo_incremental_share"],
    },
    "model": {
        "adj_r2": float(res.rsquared_adj),
        "mape": float(mmm.mape(df["Volume_Sales"], model.predict())),
        "holdout_mape": float(holdout["holdout_MAPE"]),
        "dw": float(pd.read_csv(OUT / "diagnostics.csv").iloc[0]["value"]),
        "journey": journey.round(3).to_dict(orient="records"),
        "rates": rates,
        "coefficients": [
            {"driver": mmm.DRIVER_LABELS.get(i, i), "coef": float(res.params[i]), "t": float(res.tvalues[i])}
            for i in res.params.index
            if i != "const"
        ],
    },
}

# Appendix material
data["diagnostics"] = (
    pd.read_csv(OUT / "diagnostics.csv")
    .round(4)
    .astype(object)
    .where(lambda t: t.notna(), None)
    .to_dict(orient="records")
)
data["rejected"] = pd.read_csv(OUT / "variables_rejected.csv").round(4).to_dict(orient="records")
data["fit"] = {
    "actual": (df["Volume_Sales"] / 1e6).round(3).tolist(),
    "model": (model.predict() / 1e6).round(3).tolist(),
}
cal_channels = ["TV", "VOD", "OLV", "Social", "Search", "RDM", "Online_Partnership", "OOH"]
months = df["Date"].dt.to_period("M")
data["calendar"] = {
    "months": [m.strftime("%b %y") for m in months.unique()],
    "channels": [c.replace("_", " ").replace("Partnership", "partnership") for c in cal_channels],
    "spend_k": [
        [float(df.loc[months == m, f"Media_{c}_Spends"].sum() / 1e3) for m in months.unique()]
        for c in cal_channels
    ],
}

(ROOT / "deck" / "deck_data.json").write_text(json.dumps(data, indent=1, default=float))
print("Wrote deck/deck_data.json")
