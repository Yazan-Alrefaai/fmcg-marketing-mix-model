# %% [markdown]
# # Step 1 - Load and clean the data
# Goal: get one tidy weekly table we can trust before any analysis.

# %%
import pandas as pd

from style import ROOT

RAW = ROOT / "data" / "model_variables.xlsx"
CLEAN = ROOT / "data" / "clean.csv"

df = pd.read_excel(RAW, sheet_name="Model variables")
dictionary = pd.read_excel(RAW, sheet_name="Variable dictionary")

print("Shape:", df.shape)
print("Variables by type:")
print(dictionary["Variable type"].value_counts().to_string())

# %% [markdown]
# ## Dates
# Excel stores dates as day counts since 1899-12-30 (44562 = 2022-01-01).

# %%
if not pd.api.types.is_datetime64_any_dtype(df["Date"]):
    df["Date"] = pd.to_datetime(df["Date"], unit="D", origin="1899-12-30")

df = df.sort_values("Date").reset_index(drop=True)
gaps = df["Date"].diff().dt.days.value_counts()

print("Period:", df["Date"].min().date(), "to", df["Date"].max().date())
print("Weeks:", len(df))
print("Days between consecutive rows:", gaps.to_dict())
print("Duplicate dates:", df["Date"].duplicated().sum())
print("Weekday of dates:", ", ".join(df["Date"].dt.day_name().unique()))

# %% [markdown]
# ## Data quality checks
# Missing values, negatives, and columns that are mostly zero (media is
# usually zero in weeks a channel is off air - that is normal, not an error).

# %%
numeric = df.select_dtypes("number")

missing = df.isna().sum()
negatives = (numeric < 0).sum()
zero_share = (numeric == 0).mean().round(2)

print("Missing values:", int(missing.sum()))
print("Negative values (temperatures below 0°C in winter - expected):")
print(negatives[negatives > 0].to_string())
print("\nShare of weeks at zero (media is off in most weeks - expected):")
print(zero_share[zero_share > 0].sort_values(ascending=False).to_string())

# %% [markdown]
# ## Sanity checks on definitions
# If the data is consistent, promo sales should never exceed total sales,
# and value / volume should equal the average price per kg.

# %%
checks = pd.DataFrame(
    {
        "promo_vol_gt_total": df["Promotion_Volume_Sales"] > df["Volume_Sales"],
        "price_mismatch": (df["Value_Sales"] / df["Volume_Sales"] - df["Avg_PPKG"]).abs() > 0.01,
    }
)
print("Weeks failing each check:", checks.sum().to_dict())

# Average pack size (kg per unit) tells us what product we are looking at
print("Avg kg per unit:", (df["Volume_Sales"] / df["Unit_Sales"]).describe().round(2).to_dict())

# %%
df.to_csv(CLEAN, index=False)
print("Saved clean data:", CLEAN.relative_to(ROOT))
