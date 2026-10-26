# %% [markdown]
# # Step 2 - Sales, seasonality and weather
# Questions: How big is the brand? Is it growing? When does it sell?
# How much does the weather matter for bottled water?

# %%
import matplotlib.pyplot as plt
import numpy as np

from style import INK_2, MUTED, SERIES, load, save, thousands

df = load()
df["Year"] = df["Date"].dt.year
df["Month"] = df["Date"].dt.month
# Week number from day of year (ISO weeks would put 1 Jan 2022 in week 52)
df["Week"] = (df["Date"].dt.dayofyear - 1) // 7 + 1

# %% [markdown]
# ## Size and growth per year
# 2025 has only 4 weeks, so it is excluded from yearly comparisons.

# %%
full_years = df[df["Year"] < 2025]
yearly = full_years.groupby("Year").agg(
    weeks=("Date", "count"),
    volume_kg=("Volume_Sales", "sum"),
    value_gbp=("Value_Sales", "sum"),
    promo_volume=("Promotion_Volume_Sales", "sum"),
    avg_price_kg=("Avg_PPKG", "mean"),
    avg_temp=("weather_average_temp", "mean"),
)
yearly["promo_share"] = yearly["promo_volume"] / yearly["volume_kg"]
# 2022 has 53 weekly rows and 2023/2024 have 52, so compare average weeks, not totals
yearly["avg_week_volume"] = yearly["volume_kg"] / yearly["weeks"]
yearly["avg_week_value"] = yearly["value_gbp"] / yearly["weeks"]
yearly["volume_growth"] = yearly["avg_week_volume"].pct_change()
yearly["value_growth"] = yearly["avg_week_value"].pct_change()
print(yearly.round(3).to_string())

# %% [markdown]
# ## Monthly seasonality (index: 100 = average month)

# %%
monthly = full_years.groupby("Month")[["Volume_Sales", "weather_average_temp"]].mean()
monthly["sales_index"] = 100 * monthly["Volume_Sales"] / monthly["Volume_Sales"].mean()
print(monthly.round(1).to_string())

# %% [markdown]
# ## How strongly does weather move with sales?

# %%
weather_cols = ["weather_average_temp", "weather_max_temp", "weather_min_temp", "weather_rainfall"]
print(df[["Volume_Sales"] + weather_cols].corr()["Volume_Sales"].round(2).to_string())

# Peak weeks: is it heat, promotion, or both?
df["promo_share"] = df["Promotion_Volume_Sales"] / df["Volume_Sales"]
peaks = df.nlargest(8, "Volume_Sales")[
    ["Date", "Volume_Sales", "weather_max_temp", "promo_share", "Base_Avg_PPKG"]
]
print("\nTop 8 weeks:\n", peaks.to_string(index=False, float_format="%.2f"))

# %% [markdown]
# ## Chart 1 - Weekly volume sales, total vs on promotion

# %%
fig, ax = plt.subplots(figsize=(11, 4))
ax.plot(df["Date"], df["Volume_Sales"], color=SERIES[0], label="Total volume")
ax.fill_between(
    df["Date"],
    df["Promotion_Volume_Sales"],
    color=SERIES[1],
    alpha=0.35,
    linewidth=0,
    label="Sold on promotion",
)
ax.set_title("Weekly volume sales (kg): total vs sold on promotion")
ax.set_ylim(0)
thousands(ax)
ax.legend(loc="upper left", ncol=2)
save(fig, "01_volume_sales_weekly")

# %% [markdown]
# ## Chart 2 - Sales and temperature, two panels on the same timeline
# (Two panels instead of a dual axis, so neither scale can mislead.)

# %%
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 5.5), sharex=True, gridspec_kw={"height_ratios": [3, 2]})
ax1.plot(df["Date"], df["Volume_Sales"], color=SERIES[0])
ax1.set_title("Volume sales (kg) follow temperature")
ax1.set_ylim(0)
thousands(ax1)
ax2.plot(df["Date"], df["weather_max_temp"], color=SERIES[1])
ax2.set_title("Weekly max temperature (°C)", fontsize=10, color=INK_2)
save(fig, "02_sales_and_temperature")

# %% [markdown]
# ## Chart 3 - Scatter: volume vs max temperature

# %%
x, y = df["weather_max_temp"], df["Volume_Sales"]
slope, intercept = np.polyfit(x, y, 1)
r = np.corrcoef(x, y)[0, 1]

fig, ax = plt.subplots(figsize=(6.5, 4.5))
ax.scatter(x, y, s=28, color=SERIES[0], alpha=0.75, edgecolor="white", linewidth=0.8)
xs = np.linspace(x.min(), x.max(), 50)
ax.plot(xs, intercept + slope * xs, color=MUTED, linewidth=1.5, linestyle="--")
ax.set_title(f"Hotter weeks sell more (r = {r:.2f})")
ax.set_xlabel("Weekly max temperature (°C)")
ax.set_ylabel("Volume sales (kg)")
thousands(ax)
save(fig, "03_volume_vs_temperature")

# %% [markdown]
# ## Chart 4 - Same seasonal shape every year?

# %%
fig, ax = plt.subplots(figsize=(11, 4))
for i, (year, g) in enumerate(full_years.groupby("Year")):
    ax.plot(g["Week"], g["Volume_Sales"], color=SERIES[i], label=str(year))
ax.set_title("Volume sales by week of year")
ax.set_xlabel("Week of year")
ax.set_ylim(0)
thousands(ax)
ax.legend(loc="upper left", ncol=3)
save(fig, "04_seasonality_by_year")
