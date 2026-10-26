# %% [markdown]
# # Step 7 - Results: what drives sales, and what does media return?
# 1. Decomposition: weekly volume split into base, weather, Christmas and media.
# 2. Media: incremental volume, revenue and ROI per channel (with a range).
# 3. Response curves: what happens if spend per channel goes up or down.
# 4. Year-on-year bridge: why volume fell in 2023 and recovered in 2024.
# 5. Promotions: their effect works through distribution.

# %%
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm

import mmm
from style import INK, INK_2, MUTED, ROOT, SERIES, load, save, thousands

df = load()
OUT = ROOT / "outputs"
rates = json.loads((OUT / "model_config.json").read_text())["rates"]
model = mmm.MMM(df, rates)
b = model.params
channels = model.channels
price = df["Avg_PPKG"].to_numpy()  # £ per kg actually paid, to turn kg into £

# %% [markdown]
# ## 1. Decomposition

# %%
parts = model.decompose()
totals = parts.sum()
share = totals / totals.sum()
print("Share of total volume (whole period):\n", (share * 100).round(2).to_string())
print(f"Check: parts add up to model total -> {parts.sum(axis=1).sum() / model.predict().sum():.4f}")

media_share_by_year = (
    parts[channels].sum(axis=1).groupby(parts.index.year).sum()
    / parts.sum(axis=1).groupby(parts.index.year).sum()
)
print("Media share of volume by year:\n", (media_share_by_year * 100).round(2).to_string())

colors = {"Base": "#c3c2b7", "Weather": SERIES[1], "Christmas week": SERIES[7]}
colors.update({ch: SERIES[i] for i, ch in zip([0, 2, 6, 4], channels, strict=True)})

fig, ax = plt.subplots(figsize=(11, 4.5))
positive = ["Base", "Weather"] + channels
bottom = np.zeros(len(parts))
for col in positive:
    ax.fill_between(
        parts.index, bottom, bottom + parts[col], color=colors[col], linewidth=0, label=col, step=None
    )
    bottom = bottom + parts[col]
ax.fill_between(
    parts.index,
    0,
    parts["Christmas week"],
    color=colors["Christmas week"],
    linewidth=0,
    label="Christmas week",
)
ax.plot(df["Date"], df["Volume_Sales"], color=INK, linewidth=1, label="Actual")
ax.set_title("What drives weekly volume: base and weather dominate, media adds a thin layer")
thousands(ax)
ax.legend(loc="upper left", ncol=4, fontsize=8.5)
ax.set_ylim(top=parts[positive].sum(axis=1).max() * 1.25)
save(fig, "14_decomposition_weekly")

# %% [markdown]
# ## 2. Media incremental volume, revenue and ROI
# ROI = incremental revenue (£) / spend (£). Revenue ROI, not profit: we have no margin data.
# Range: re-computed with the coefficient at its 95% confidence bounds (floored at zero).

# %%
spend = model.actual_spend()
rows = []
for ch in channels:
    inc = model.channel_incremental(ch)
    lo_coef = max(b[ch] - 1.96 * model.res.bse[ch], 0)
    hi_coef = b[ch] + 1.96 * model.res.bse[ch]
    inc_lo = model.channel_incremental(ch, coef=lo_coef)
    inc_hi = model.channel_incremental(ch, coef=hi_coef)
    total_spend = spend[ch].sum()
    rows.append(
        {
            "channel": ch,
            "spend": total_spend,
            "incremental_kg": inc.sum(),
            "incremental_revenue": (inc * price).sum(),
            "roi": (inc * price).sum() / total_spend,
            "roi_low": (inc_lo * price).sum() / total_spend,
            "roi_high": (inc_hi * price).sum() / total_spend,
            "t_stat": model.res.tvalues[ch],
            "carryover_rate": rates[ch],
        }
    )
media = pd.DataFrame(rows).set_index("channel")
media["share_of_spend"] = media["spend"] / media["spend"].sum()
media["share_of_media_volume"] = media["incremental_kg"] / media["incremental_kg"].sum()
total_row = media[["spend", "incremental_kg", "incremental_revenue"]].sum()
print(media.round(3).to_string())
print(
    f"\nAll modelled media: spend £{total_row['spend']:,.0f}, "
    f"incremental revenue £{total_row['incremental_revenue']:,.0f}, "
    f"ROI £{total_row['incremental_revenue'] / total_row['spend']:.2f} per £1"
)
excluded = {ch: mmm.channel_spend(df, ch).sum() for ch in ["Social", "Search", "RDM"]}
print("Spend not measurable in the model:", {k: f"£{v:,.0f}" for k, v in excluded.items()})

order = media.sort_values("roi").index
fig, ax = plt.subplots(figsize=(8, 3.8))
y_pos = np.arange(len(order))
ax.barh(y_pos, media.loc[order, "roi"], color=SERIES[0], height=0.55)
ax.errorbar(
    media.loc[order, "roi"],
    y_pos,
    xerr=[
        media.loc[order, "roi"] - media.loc[order, "roi_low"],
        media.loc[order, "roi_high"] - media.loc[order, "roi"],
    ],
    fmt="none",
    ecolor=INK_2,
    elinewidth=1,
    capsize=3,
)
for i, ch in enumerate(order):
    ax.annotate(
        f"£{media.loc[ch, 'roi']:.2f}",
        (media.loc[ch, "roi_high"], i),
        xytext=(6, 0),
        textcoords="offset points",
        va="center",
        fontsize=9,
        color=INK_2,
    )
ax.axvline(1, color=MUTED, linewidth=1, linestyle="--")
ax.annotate(
    "break-even £1",
    (1, len(order) - 0.45),
    xytext=(4, 0),
    textcoords="offset points",
    fontsize=8,
    color=MUTED,
)
ax.set_yticks(y_pos, order)
ax.set_title("Revenue return per £1 of media (bar = estimate, line = 95% range)")
ax.grid(axis="y", visible=False)
ax.set_xlim(0, media["roi_high"].max() * 1.25)
save(fig, "15_media_roi")

fig, ax = plt.subplots(figsize=(8, 3.6))
w = 0.38
spend_share = media.loc[order, "share_of_spend"] * 100
vol_share = media.loc[order, "share_of_media_volume"] * 100
ax.barh(y_pos + w / 2, spend_share, height=w, color=SERIES[3], label="Share of spend")
ax.barh(y_pos - w / 2, vol_share, height=w, color=SERIES[0], label="Share of media-driven sales")
for i in range(len(order)):
    ax.annotate(
        f"{spend_share.iloc[i]:.0f}%",
        (spend_share.iloc[i], i + w / 2),
        xytext=(4, 0),
        textcoords="offset points",
        va="center",
        fontsize=8.5,
        color=INK_2,
    )
    ax.annotate(
        f"{vol_share.iloc[i]:.0f}%",
        (vol_share.iloc[i], i - w / 2),
        xytext=(4, 0),
        textcoords="offset points",
        va="center",
        fontsize=8.5,
        color=INK_2,
    )
ax.set_yticks(y_pos, order)
ax.set_title("Share of spend vs share of media-driven sales")
ax.grid(axis="y", visible=False)
ax.legend(loc="lower right")
save(fig, "16_spend_vs_effect_share")

# %% [markdown]
# ## 3. Response curves
# Scale each channel's actual weekly plan (same weeks, same shape) from 0x to 3x
# and measure incremental revenue. The slope at 1x is the marginal ROI:
# what the NEXT £1 would return.

# %%
multipliers = np.linspace(0, 3, 31)
curves = {}
for ch in channels:
    rev = []
    for k in multipliers:
        s = {**spend, ch: spend[ch] * k}
        rev.append((model.channel_incremental(ch, spend=s) * price).sum())
    curves[ch] = pd.Series(rev, index=multipliers * spend[ch].sum())
for ch in channels:
    s = {**spend, ch: spend[ch] * 1.1}
    extra = (model.channel_incremental(ch, spend=s) * price).sum() - media.loc[ch, "incremental_revenue"]
    media.loc[ch, "marginal_roi"] = extra / (0.1 * spend[ch].sum())
print(media[["roi", "marginal_roi"]].round(2).to_string())

fig, ax = plt.subplots(figsize=(8, 4.5))
for ch in channels:
    c = curves[ch]
    ax.plot(c.index, c.values, color=colors[ch], label=ch)
    ax.scatter(
        [spend[ch].sum()],
        [media.loc[ch, "incremental_revenue"]],
        color=colors[ch],
        s=40,
        zorder=3,
        edgecolor="white",
    )
ax.set_title("Response curves: incremental revenue vs total spend (dot = actual spend)")
ax.set_xlabel("Total spend (£)")
ax.set_ylabel("Incremental revenue (£)")
thousands(ax)
thousands(ax, axis="x")
ax.legend(loc="upper left")
save(fig, "17_response_curves")

# %% [markdown]
# ## Budget scenarios (same total budget)
# Move 30% of the TV and Online video budgets (lowest marginal ROI) into the
# channels with the highest marginal ROI. New money is added in the weeks those
# channels already ran, in proportion to their existing plan.


# %%
def move_budget(source, target, pct=0.3):
    moved = {ch: pct * spend[ch] for ch in source}
    amount = sum(v.sum() for v in moved.values())
    new = {ch: spend[ch] - moved.get(ch, 0) for ch in channels}
    new[target] = spend[target] + amount * spend[target] / spend[target].sum()
    delta = ((model.predict(model.with_spend(new)) - model.predict(model.with_spend(spend))) * price).sum()
    return amount, delta


scenarios = {}
for target in ["Online partnership", "OOH"]:
    amount, delta = move_budget(["TV", "Online video"], target)
    scenarios[target] = {"moved": amount, "delta_revenue": delta}
    print(
        f"Move £{amount:,.0f} from TV + Online video into {target}: revenue {delta:+,.0f} "
        f"({delta / media['incremental_revenue'].sum():+.0%} of media-driven revenue)"
    )

# %% [markdown]
# ## 4. Year-on-year bridge
# In a log model, the change in average log volume splits exactly into
# coefficient x change in each driver's average. 100 x log points ~ % change.

# %%
yr = df["Date"].dt.year
groups = {
    "Weather": ["max_temp", "hot_degrees", "rainfall"],
    "Christmas timing": ["xmas_week"],
    "Relative price": ["ln_relative_price"],
    "Distribution": ["distribution_acv"],
    "Media": channels,
}
means = model.X.groupby(yr).mean()
resid_mean = model.res.resid.groupby(yr).mean()
bridge = {}
for a, c in [(2022, 2023), (2023, 2024)]:
    row = {g: 100 * sum(b[v] * (means.loc[c, v] - means.loc[a, v]) for v in vs) for g, vs in groups.items()}
    row["Unexplained"] = 100 * (resid_mean[c] - resid_mean[a])
    row["Total (log pts)"] = 100 * (
        np.log(df.loc[yr == c, "Volume_Sales"]).mean() - np.log(df.loc[yr == a, "Volume_Sales"]).mean()
    )
    bridge[f"{a}->{c}"] = row
bridge = pd.DataFrame(bridge)
print(bridge.round(1).to_string())
print(
    "Driver averages by year:\n",
    means[["max_temp", "hot_degrees", "rainfall", "ln_relative_price", "distribution_acv"]]
    .round(3)
    .to_string(),
)

fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
for ax, col in zip(axes, bridge.columns, strict=True):
    vals = bridge[col].drop("Total (log pts)")
    cols = [SERIES[0] if v >= 0 else SERIES[7] for v in vals]
    ax.barh(vals.index[::-1], vals.values[::-1], color=cols[::-1], height=0.55)
    for i, v in enumerate(vals.values[::-1]):
        ax.annotate(
            f"{v:+.1f}",
            (v, i),
            xytext=(4 if v >= 0 else -4, 0),
            textcoords="offset points",
            ha="left" if v >= 0 else "right",
            va="center",
            fontsize=9,
            color=INK_2,
        )
    ax.axvline(0, color=INK_2, linewidth=0.8)
    ax.set_title(
        f"{col.replace('->', ' to ')}: volume {bridge.loc['Total (log pts)', col]:+.1f}%", fontsize=11
    )
    ax.grid(axis="y", visible=False)
    lim = (
        max(abs(bridge.drop("Total (log pts)").values.min()), bridge.drop("Total (log pts)").values.max())
        * 1.4
    )
    ax.set_xlim(-lim, lim)
fig.suptitle(
    "Why volume changed year on year (contribution, ~% points)", x=0.01, y=1.02, ha="left", fontweight="bold"
)
save(fig, "18_volume_bridge")

# %% [markdown]
# ## 5. Promotions work through distribution
# In the model, promo variables add nothing once distribution is included.
# But promotions raise distribution: more stores sell the product when it is on deal.

# %%
link = sm.OLS(
    df["ACV_Weighted_Distribution_wtd"],
    sm.add_constant(
        pd.DataFrame(
            {"promo_acv": df["Promotion_ACV_Weighted_Distribution_wtd"], "trend": np.arange(len(df)) / 52}
        )
    ),
).fit(cov_type="HAC", cov_kwds={"maxlags": 4})
per_point = link.params["promo_acv"]
promo_effect_per_point = np.exp(per_point * b["distribution_acv"]) - 1
avg_promo_acv = df["Promotion_ACV_Weighted_Distribution_wtd"].mean()
promo_total = np.exp(per_point * b["distribution_acv"] * avg_promo_acv) - 1
print(
    f"+1 point promo ACV -> +{per_point:.2f} points total ACV (t {link.tvalues['promo_acv']:.1f}) "
    f"-> +{promo_effect_per_point:.2%} volume"
)
print(
    f"Average promo ACV {avg_promo_acv:.1f} points -> promotions lift volume "
    f"~{promo_total:.1%} via distribution"
)
promo_share = df["Promotion_Volume_Sales"].sum() / df["Volume_Sales"].sum()
print(f"Share of volume sold on promotion: {promo_share:.1%}")
print(
    f"=> about {promo_total / (1 + promo_total) / promo_share:.0%} of promoted volume looks incremental; "
    "the rest would have sold at full price"
)

depth_by_year = (
    (1 - df["Promotion_Avg_PPKG"] / df["Base_Avg_PPKG"])
    .where(df["Promotion_Volume_Sales"] / df["Volume_Sales"] >= 0.05)
    .groupby(yr)
    .mean()
)
print("Average promo discount by year:", (depth_by_year * 100).round(1).to_dict())

# %%
media.to_csv(OUT / "media_roi.csv")
bridge.to_csv(OUT / "volume_bridge.csv")
parts.to_csv(OUT / "decomposition_weekly.csv")
pd.DataFrame(curves).to_csv(OUT / "response_curves.csv")
summary = {
    "share_of_volume": (share * 100).round(2).to_dict(),
    "media_total_roi": float(total_row["incremental_revenue"] / total_row["spend"]),
    "promo_lift_via_distribution": float(promo_total),
    "promo_incremental_share": float(promo_total / (1 + promo_total) / promo_share),
    "scenarios": scenarios,
}
(OUT / "results_summary.json").write_text(json.dumps(summary, indent=2))
