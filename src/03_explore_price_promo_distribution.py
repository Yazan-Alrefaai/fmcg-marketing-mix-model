# %% [markdown]
# # Step 3 - Price, promotion and distribution
# Questions: How did pricing change? How deep and how frequent are promotions?
# Is the brand on shelf everywhere, or does distribution move?

# %%
import matplotlib.pyplot as plt

from style import INK_2, SERIES, load, save, thousands

df = load()
df["Year"] = df["Date"].dt.year

# Promo depth: how much cheaper the promo price is than the normal shelf price
df["promo_depth"] = 1 - df["Promotion_Avg_PPKG"] / df["Base_Avg_PPKG"]
df["promo_share"] = df["Promotion_Volume_Sales"] / df["Volume_Sales"]

# %% [markdown]
# ## Price and promo by year

# %%
yearly = (
    df[df["Year"] < 2025]
    .groupby("Year")
    .agg(
        base_price_kg=("Base_Avg_PPKG", "mean"),
        promo_price_kg=("Promotion_Avg_PPKG", "mean"),
        avg_price_kg=("Avg_PPKG", "mean"),
        promo_depth=("promo_depth", "mean"),
        promo_share=("promo_share", "mean"),
        promo_acv=("Promotion_ACV_Weighted_Distribution_wtd", "mean"),
        acv_wtd=("ACV_Weighted_Distribution_wtd", "mean"),
        acv_max=("ACV_Weighted_Distribution_max", "mean"),
        stores=("Number_of_Stores_Selling", "mean"),
    )
)
print(yearly.round(3).to_string())

# %% [markdown]
# ## When did the base price change?
# Print weeks where the base price moved more than 3% vs the previous week.

# %%
jumps = df.loc[df["Base_Avg_PPKG"].pct_change().abs() > 0.03, ["Date", "Base_Avg_PPKG"]]
jumps["change"] = df["Base_Avg_PPKG"].pct_change()[jumps.index]
print(jumps.to_string(index=False, float_format="%.3f"))

# %% [markdown]
# ## Distribution: does it vary enough to explain anything?

# %%
dist_cols = [
    "ACV_Weighted_Distribution_wtd",
    "ACV_Weighted_Distribution_max",
    "Number_of_Stores_Selling",
    "Promotion_ACV_Weighted_Distribution_wtd",
]
print(df[dist_cols].describe().round(2).to_string())

# %% [markdown]
# ## Correlation with volume (simple, no controls yet - weather is mixed in!)

# %%
cols = [
    "Base_Avg_PPKG",
    "Avg_PPKG",
    "promo_depth",
    "promo_share",
    "Promotion_ACV_Weighted_Distribution_wtd",
    "ACV_Weighted_Distribution_wtd",
    "Number_of_Stores_Selling",
]
print(df[["Volume_Sales"] + cols].corr()["Volume_Sales"].round(2).to_string())

# %% [markdown]
# ## Chart 5 - Base price vs promo price per kg

# %%
fig, ax = plt.subplots(figsize=(11, 4))
ax.plot(df["Date"], df["Base_Avg_PPKG"], color=SERIES[0], label="Base price")
ax.plot(df["Date"], df["Promotion_Avg_PPKG"], color=SERIES[1], label="Promo price")
ax.set_title("Price per kg (£): base price rose sharply, promo price followed")
ax.set_ylim(0)
ax.legend(loc="upper left", ncol=2)
save(fig, "05_price_base_vs_promo")

# %% [markdown]
# ## Chart 6 - Promotion intensity: share of volume on promo and discount depth

# %%
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 5.5), sharex=True)
ax1.plot(df["Date"], df["promo_share"] * 100, color=SERIES[1])
ax1.set_title("Share of volume sold on promotion (%)")
ax1.set_ylim(0)
# Promo price is unreliable when almost nothing sells on promo (it even goes above
# base price in summer 2022), so hide weeks with under 5% of volume on promo.
reliable_depth = df["promo_depth"].where(df["promo_share"] >= 0.05)
ax2.plot(df["Date"], reliable_depth * 100, color=SERIES[2])
ax2.set_title(
    "Promo discount vs base price (%) - weeks with at least 5% volume on promo", fontsize=10, color=INK_2
)
ax2.set_ylim(0)
save(fig, "06_promo_intensity")

# %% [markdown]
# ## Chart 7 - Distribution over time

# %%
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 5.5), sharex=True)
ax1.plot(df["Date"], df["ACV_Weighted_Distribution_wtd"], color=SERIES[0], label="ACV weighted (wtd)")
ax1.plot(
    df["Date"], df["Promotion_ACV_Weighted_Distribution_wtd"], color=SERIES[1], label="ACV on promotion (wtd)"
)
ax1.set_title("Weighted distribution (% ACV)")
ax1.set_ylim(0, 60)
ax1.legend(loc="upper left", ncol=2)
ax2.plot(df["Date"], df["Number_of_Stores_Selling"], color=SERIES[2])
ax2.set_title("Number of stores selling", fontsize=10, color=INK_2)
thousands(ax2)
save(fig, "07_distribution")
