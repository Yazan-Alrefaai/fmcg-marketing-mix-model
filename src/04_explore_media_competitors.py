# %% [markdown]
# # Step 4 - Media and competitors
# Questions: How much was spent per channel, and when? Which channels run at the
# same time (hard for a model to separate)? What are competitors doing?

# %%
import matplotlib.pyplot as plt
import pandas as pd

from style import INK_2, SERIES, load, save, thousands

df = load()

CHANNELS = ["TV", "VOD", "OLV", "Social", "Search", "RDM", "Online_Partnership", "OOH"]
spend_cols = {c: f"Media_{c}_Spends" for c in CHANNELS}
activity_cols = {
    "TV": "Media_TV_GRPs",
    "VOD": "Media_VOD_Impressions",
    "OLV": "Media_OLV_Impressions",
    "Social": "Media_Social_Impressions",
    "Search": "Media_Search_Impressions",
    "RDM": "Media_RDM_Impressions",
}

# %% [markdown]
# ## Budget summary per channel

# %%
rows = []
for c, col in spend_cols.items():
    s = df[col]
    on = s > 0
    rows.append(
        {
            "channel": c,
            "total_spend": s.sum(),
            "active_weeks": int(on.sum()),
            "first_week": df.loc[on, "Date"].min().date(),
            "last_week": df.loc[on, "Date"].max().date(),
            "avg_spend_when_on": s[on].mean(),
        }
    )
summary = pd.DataFrame(rows).set_index("channel").sort_values("total_spend", ascending=False)
summary["share_of_budget"] = summary["total_spend"] / summary["total_spend"].sum()
print(summary.round(2).to_string())
print("\nTotal media spend: £{:,.0f}".format(summary["total_spend"].sum()))
print("Total value sales: £{:,.0f}".format(df["Value_Sales"].sum()))

# Cost per thousand impressions (CPM) / cost per GRP, where activity exists
for c, col in activity_cols.items():
    on = df[spend_cols[c]] > 0
    cost = df.loc[on, spend_cols[c]].sum() / df.loc[on, col].sum()
    unit = "per GRP" if c == "TV" else "per 1,000 impressions"
    print(f"{c:7s} cost {unit}: £{cost * (1 if c == 'TV' else 1000):,.2f}")

# %% [markdown]
# ## Media calendar: which weeks is each channel on air?

# %%
calendar = pd.DataFrame({c: (df[col] > 0).astype(int) for c, col in spend_cols.items()})
calendar.index = df["Date"].dt.strftime("%Y-%m-%d")
print(calendar[calendar.sum(axis=1) > 0].to_string())

# %% [markdown]
# ## Channels on air together (count of overlapping active weeks)

# %%
on_air = calendar.astype(bool)
overlap = pd.DataFrame({a: {b: int((on_air[a] & on_air[b]).sum()) for b in CHANNELS} for a in CHANNELS})
print(overlap.to_string())

# %% [markdown]
# ## Competitors: sales, price and media

# %%
comp = pd.DataFrame({"Our brand": df["Volume_Sales"]})
for b in ["A", "B", "C"]:
    comp[f"Brand {b}"] = df[f"Comp_Brand_{b}_Volume_Sales"]
print("Average weekly volume (kg):\n", comp.mean().round(0).to_string())
print("\nVolume share:\n", (comp.mean() / comp.mean().sum()).round(3).to_string())

prices = pd.DataFrame({"Our brand": df["Base_Avg_PPKG"]})
for b in ["A", "B", "C"]:
    prices[f"Brand {b}"] = df[f"Comp_Brand_{b}_Base_Avg_PPKG"]
print("\nAverage base price per kg:\n", prices.mean().round(3).to_string())

comp_media = [c for c in df.columns if c.startswith("Comp_") and c.endswith("Media_Spends")]
for c in comp_media:
    print(f"{c}: total £{df[c].sum():,.0f}, active weeks {(df[c] > 0).sum()}")

print("\nCorrelation of competitor volumes with ours:\n", comp.corr()["Our brand"].round(2).to_string())

# %% [markdown]
# ## Chart 8 - Media spend by channel (share of total budget)

# %%
order = summary.index.tolist()
fig, ax = plt.subplots(figsize=(8, 4))
labels = [c.replace("_", " ") for c in order[::-1]]
ax.barh(labels, summary["total_spend"][::-1], color=SERIES[0], height=0.6)
for i, (c, v) in enumerate(summary["total_spend"][::-1].items()):
    ax.annotate(
        f"£{v / 1e3:,.0f}k  ({summary.loc[c, 'share_of_budget']:.0%}, {summary.loc[c, 'active_weeks']} wks)",
        (v, i),
        xytext=(4, 0),
        textcoords="offset points",
        va="center",
        fontsize=9,
        color=INK_2,
    )
ax.set_title("Total media spend by channel, 2022-2025")
ax.grid(axis="y", visible=False)
thousands(ax, axis="x")
ax.set_xlim(0, summary["total_spend"].max() * 1.45)
save(fig, "08_media_spend_by_channel")

# %% [markdown]
# ## Chart 9 - Media flighting: weekly spend per channel on one timeline
# Small multiples (one row per channel) so bursts are easy to compare.

# %%
fig, axes = plt.subplots(len(order), 1, figsize=(11, 8), sharex=True)
for ax, c in zip(axes, order, strict=True):
    ax.bar(df["Date"], df[spend_cols[c]], width=6, color=SERIES[0])
    ax.set_ylabel(c.replace("_", " "), rotation=0, ha="right", va="center", fontsize=9, color=INK_2)
    ax.set_yticks([])
    ax.grid(False)
    ax.spines["left"].set_visible(False)
axes[0].set_title("When each channel was on air (weekly spend, each row on its own scale)")
save(fig, "09_media_flighting")

# %% [markdown]
# ## Chart 10 - Our volume vs competitors

# %%
fig, ax = plt.subplots(figsize=(11, 4))
for i, col in enumerate(comp.columns):
    ax.plot(df["Date"], comp[col], color=SERIES[i], label=col, linewidth=2 if i == 0 else 1.5)
ax.set_title("Weekly volume sales (kg): our brand vs competitors")
ax.set_ylim(0)
thousands(ax)
ax.legend(loc="upper left", ncol=4)
save(fig, "10_competitor_volume")
