# %% [markdown]
# # Step 6 - Can we trust the model?
# 1. Holdout test: fit without the last 12 weeks, then predict them.
# 2. Residual checks: errors should look like random noise.
# 3. Multicollinearity (VIF).
# 4. Stability: do the main coefficients hold if we drop a year?
# 5. Sensitivity: how much do key results move under reasonable alternatives?

# %%
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.diagnostic import acorr_breusch_godfrey, het_breuschpagan
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.stattools import durbin_watson, jarque_bera

import mmm
from style import INK_2, MUTED, ROOT, SERIES, load, save, thousands

df = load()
OUT = ROOT / "outputs"
rates = json.loads((OUT / "model_config.json").read_text())["rates"]
model = mmm.MMM(df, rates)
res = model.res

# %% [markdown]
# ## 1. Holdout test (last 12 weeks)
# The whole pipeline is re-run on the first 149 weeks only: carryover search,
# saturation scales and coefficients. The last 12 weeks are never seen.

# %%
HOLDOUT = 12
train = df.index < len(df) - HOLDOUT
train_df = df[train].reset_index(drop=True)
y_all = np.log(df["Volume_Sales"])

rates_train = (
    mmm.search_adstock(
        train_df, np.log(train_df["Volume_Sales"]), mmm.base_features(train_df), list(mmm.MEDIA)
    )
    or rates
)
scales_train = {}
for ch, r in rates_train.items():
    a = mmm.adstock(mmm.channel_spend(df, ch), r)[train]
    scales_train[ch] = a[a > 0].mean()
X_all = pd.concat([mmm.base_features(df), mmm.media_features(df, rates_train, scales_train)], axis=1)

res_train = mmm.fit_ols(y_all[train], X_all[train])
smear = np.mean(np.exp(res_train.resid))
pred_all = np.exp(res_train.params["const"] + X_all @ res_train.params[X_all.columns]) * smear
print("Carryover rates chosen on training weeks:", rates_train, "(full data:", rates, ")")

mape_train = mmm.mape(df.loc[train, "Volume_Sales"], pred_all[train])
mape_test = mmm.mape(df.loc[~train, "Volume_Sales"], pred_all[~train])
bias_test = (pred_all[~train].sum() / df.loc[~train, "Volume_Sales"].sum()) - 1
print(
    f"Training MAPE: {mape_train:.1%}   Holdout MAPE: {mape_test:.1%}   Holdout total bias: {bias_test:+.1%}"
)

fig, ax = plt.subplots(figsize=(11, 4))
ax.plot(df["Date"], df["Volume_Sales"], color=SERIES[0], label="Actual")
ax.plot(df["Date"][train], pred_all[train], color=SERIES[1], linewidth=1.6, label="Model (training weeks)")
ax.plot(
    df["Date"][~train],
    pred_all[~train],
    color=SERIES[1],
    linewidth=2,
    linestyle="--",
    label="Model forecast (holdout)",
)
ax.axvspan(df["Date"][~train].min(), df["Date"].max(), color=MUTED, alpha=0.12, linewidth=0)
ax.set_title(f"Holdout test: model forecasts unseen last 12 weeks with {mape_test:.1%} average error")
ax.set_ylim(0)
thousands(ax)
ax.legend(loc="upper left", ncol=3)
save(fig, "12_holdout_test")

# %% [markdown]
# ## 2. Residual checks
# - Durbin-Watson ~2 means no week-to-week correlation in errors (below 2 = positive correlation).
# - Breusch-Godfrey: formal test for autocorrelation (small p = autocorrelation present).
# - Breusch-Pagan: are errors bigger in some weeks than others? (small p = yes).
# - Jarque-Bera: are errors normally distributed? (small p = no).

# %%
resid = res.resid
X_const = sm.add_constant(model.X)
ols_plain = sm.OLS(model.y, X_const).fit()
bg = acorr_breusch_godfrey(ols_plain, nlags=4, result_object=False)
bp = het_breuschpagan(resid, X_const)
jb = jarque_bera(resid)
diagnostics = pd.DataFrame(
    [
        {"check": "Durbin-Watson", "value": durbin_watson(resid), "p_value": np.nan},
        {"check": "Breusch-Godfrey (4 lags)", "value": bg[0], "p_value": bg[1]},
        {"check": "Breusch-Pagan", "value": bp[0], "p_value": bp[1]},
        {"check": "Jarque-Bera", "value": jb[0], "p_value": jb[1]},
        {"check": "Residual std (log points)", "value": resid.std(), "p_value": np.nan},
    ]
)
print(diagnostics.round(4).to_string(index=False))
print("Autocorrelation of residuals, lags 1-4:", [round(float(resid.autocorr(k)), 2) for k in range(1, 5)])

largest = (
    pd.DataFrame({"Date": df["Date"], "resid_pct": np.exp(resid) - 1})
    .reindex(resid.abs().sort_values(ascending=False).index)
    .head(6)
)
print("Largest misses (actual vs model):\n", largest.to_string(index=False, float_format="%.3f"))

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 3.6), gridspec_kw={"width_ratios": [3, 1]})
ax1.bar(df["Date"], (np.exp(resid) - 1) * 100, width=6, color=SERIES[0])
ax1.axhline(0, color=INK_2, linewidth=0.8)
ax1.set_title("Model error by week (% actual vs model): no clear pattern left")
ax2.hist(resid * 100, bins=20, color=SERIES[0], edgecolor="white")
ax2.set_title("Error distribution (%)", fontsize=10, color=INK_2)
save(fig, "13_residuals")

# %% [markdown]
# ## 3. Multicollinearity (VIF)
# VIF above ~5-10 means a variable is largely explained by the others,
# so its own coefficient is unreliable.

# %%
vif = pd.Series(
    {c: variance_inflation_factor(X_const.values, i) for i, c in enumerate(X_const.columns) if c != "const"}
)
print(vif.round(1).to_string())

# %% [markdown]
# ## 4. Stability: leave one year out
# Media channels only ran in one or two years, so this check is for the base drivers.

# %%
years = df["Date"].dt.year.clip(upper=2024)  # January 2025 weeks join 2024
stability = {"All weeks": res.params[mmm.BASE_DRIVERS]}
for yr in [2022, 2023, 2024]:
    keep = years != yr
    r = mmm.fit_ols(model.y[keep], model.X.loc[keep, mmm.BASE_DRIVERS])
    stability[f"Without {yr}"] = r.params[mmm.BASE_DRIVERS]
stability = pd.DataFrame(stability)
print(stability.round(4).to_string())

# %% [markdown]
# ## 5. Sensitivity of key results
# a) Price elasticity if we also add a time trend (trend and relative price both rise over time)
# b) Media coefficients if every channel used the same middle carryover (0.5)

# %%
X_trend = model.X.copy()
X_trend["trend"] = np.arange(len(df)) / 52
r_trend = mmm.fit_ols(model.y, X_trend)
print(
    f"Price elasticity: final {res.params['ln_relative_price']:.2f}, "
    f"with trend {r_trend.params['ln_relative_price']:.2f} "
    f"(trend coef {r_trend.params['trend']:.3f}/yr, t {r_trend.tvalues['trend']:.1f})"
)

alt = mmm.MMM(df, {ch: 0.5 for ch in rates})
sens = pd.DataFrame(
    {
        "final_coef": res.params[list(rates)],
        "final_t": res.tvalues[list(rates)],
        "all_0.5_coef": alt.res.params[list(rates)],
        "all_0.5_t": alt.res.tvalues[list(rates)],
    }
)
print(sens.round(4).to_string())

# %%
diagnostics.to_csv(OUT / "diagnostics.csv", index=False)
vif.rename("VIF").to_csv(OUT / "vif.csv")
stability.to_csv(OUT / "stability_leave_one_year_out.csv")
pd.DataFrame([{"train_MAPE": mape_train, "holdout_MAPE": mape_test, "holdout_bias": bias_test}]).to_csv(
    OUT / "holdout.csv", index=False
)
