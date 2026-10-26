# %% [markdown]
# # Step 5 - Build the model
# We add drivers one group at a time and watch how much each one explains.
# Then we choose media carryover rates and fit the final model.

# %%
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.stats.stattools import durbin_watson

import mmm
from style import ROOT, SERIES, load, save, thousands

df = load()
y = np.log(df["Volume_Sales"])
X_base = mmm.base_features(df)
OUT = ROOT / "outputs"

# %% [markdown]
# ## Model-building journey
# Each stage adds a group of drivers. Adjusted R² only rises if a driver
# explains more than it costs in complexity.

# %%
stages = [
    ("1. Temperature only", ["max_temp"]),
    ("2. + hot weeks, rain, Christmas", ["max_temp", "hot_degrees", "rainfall", "xmas_week"]),
    ("3. + relative price", ["max_temp", "hot_degrees", "rainfall", "xmas_week", "ln_relative_price"]),
    ("4. + distribution", mmm.BASE_DRIVERS),
]
journey = []
for name, cols in stages:
    res = mmm.fit_ols(y, X_base[cols])
    journey.append(
        {
            "stage": name,
            "adj_R2": res.rsquared_adj,
            "MAPE": mmm.mape(df["Volume_Sales"], np.exp(res.fittedvalues)),
            "DW": durbin_watson(res.resid),
            "AIC": res.aic,
        }
    )

# %% [markdown]
# ## Media carryover (adstock) rates
# Grid search over business-sense ranges; keep the best AIC where all media
# effects are positive.

# %%
channels = list(mmm.MEDIA)
rates = mmm.search_adstock(df, y, X_base, channels)
print("Chosen weekly carryover rates:", rates)
half_life = {ch: (np.log(0.5) / np.log(r) if r > 0 else 0) for ch, r in rates.items()}
print("Half-life in weeks:", {k: round(float(v), 1) for k, v in half_life.items()})

model = mmm.MMM(df, rates)
res = model.res
journey.append(
    {
        "stage": "5. + media (final model)",
        "adj_R2": res.rsquared_adj,
        "MAPE": mmm.mape(df["Volume_Sales"], model.predict()),
        "DW": durbin_watson(res.resid),
        "AIC": res.aic,
    }
)
journey = pd.DataFrame(journey)
print(journey.round(3).to_string(index=False))

# %% [markdown]
# ## Final model coefficients
# How to read them (log model):
# - a unit driver: +1 unit changes volume by about (exp(coef) - 1) %
# - ln(relative price): the coefficient is the price elasticity
# - media: effect in an average on-air week (adstock = its scale, so log(1 + 1) = 0.69)

# %%
print(res.summary())

coef = pd.DataFrame({"coef": res.params, "std_err": res.bse, "t": res.tvalues, "p_value": res.pvalues})
effects = {
    "max_temp": ("+1°C", np.exp(res.params["max_temp"]) - 1),
    "hot_degrees": (f"+1°C above {mmm.HOT_THRESHOLD}°C (extra)", np.exp(res.params["hot_degrees"]) - 1),
    "rainfall": ("+10 mm rain", np.exp(10 * res.params["rainfall"]) - 1),
    "xmas_week": ("Christmas / New Year week", np.exp(res.params["xmas_week"]) - 1),
    "ln_relative_price": ("+10% price vs competitors", 1.1 ** res.params["ln_relative_price"] - 1),
    "distribution_acv": ("+1 point ACV distribution", np.exp(res.params["distribution_acv"]) - 1),
}
for ch in channels:
    effects[ch] = ("average on-air week", np.exp(res.params[ch] * np.log(2)) - 1)
coef["meaning"] = [effects.get(i, ("", np.nan))[0] for i in coef.index]
coef["volume_effect"] = [effects.get(i, ("", np.nan))[1] for i in coef.index]
coef["confidence"] = pd.cut(coef["t"].abs(), [0, 1, 2, np.inf], labels=["low", "medium", "high"])
print(coef.round(4).to_string())

# %% [markdown]
# ## Variables tested and rejected
# Each candidate is added on top of the final model to show why it is not in it.

# %%
share = df["Promotion_Volume_Sales"] / df["Volume_Sales"]
candidates = {
    "Promo ACV distribution": df["Promotion_ACV_Weighted_Distribution_wtd"],
    "Promo discount depth (%)": (100 * (1 - df["Promotion_Avg_PPKG"] / df["Base_Avg_PPKG"]))
    .where(share >= 0.05, 0)
    .clip(lower=0),
    "Linear trend (per year)": pd.Series(np.arange(len(df)) / 52, index=df.index),
    "Competitor A media": pd.Series(
        mmm.saturate(
            mmm.adstock(df["Comp_Brand_A_Media_Spends"].to_numpy(float), 0.5),
            mmm.saturation_scale(df["Comp_Brand_A_Media_Spends"].to_numpy(float), 0.5),
        ),
        index=df.index,
    ),
    "Competitor B media": pd.Series(
        mmm.saturate(
            mmm.adstock(df["Comp_Brand_B_Media_Spends"].to_numpy(float), 0.5),
            mmm.saturation_scale(df["Comp_Brand_B_Media_Spends"].to_numpy(float), 0.5),
        ),
        index=df.index,
    ),
}
for ch, r in [("Social", 0.3), ("Search", 0.3), ("RDM", 0.3)]:
    s = mmm.channel_spend(df, ch)
    candidates[f"{ch} media"] = pd.Series(
        mmm.saturate(mmm.adstock(s, r), mmm.saturation_scale(s, r)), index=df.index
    )

rejected = []
for name, series in candidates.items():
    X_try = model.X.copy()
    X_try["candidate"] = series
    r = mmm.fit_ols(y, X_try)
    rejected.append(
        {
            "variable": name,
            "coef": r.params["candidate"],
            "t": r.tvalues["candidate"],
            "adj_R2_with": r.rsquared_adj,
            "adj_R2_without": res.rsquared_adj,
        }
    )
rejected = pd.DataFrame(rejected)
print(rejected.round(4).to_string(index=False))

# %%
journey.to_csv(OUT / "model_journey.csv", index=False)
coef.to_csv(OUT / "model_coefficients.csv")
rejected.to_csv(OUT / "variables_rejected.csv", index=False)
(OUT / "model_summary.txt").write_text(str(res.summary()))
(OUT / "model_config.json").write_text(json.dumps({"rates": rates}, indent=2))
print("Saved model outputs to", OUT.relative_to(ROOT))

# %% [markdown]
# ## Chart 11 - Actual vs model

# %%
fig, ax = plt.subplots(figsize=(11, 4))
ax.plot(df["Date"], df["Volume_Sales"], color=SERIES[0], label="Actual")
ax.plot(df["Date"], model.predict(), color=SERIES[1], label="Model", linewidth=1.6)
ax.set_title(
    f"The model tracks weekly sales closely (adjusted R² {res.rsquared_adj:.2f}, "
    f"average error {mmm.mape(df['Volume_Sales'], model.predict()):.1%})"
)
ax.set_ylim(0)
thousands(ax)
ax.legend(loc="upper left", ncol=2)
save(fig, "11_actual_vs_model")
