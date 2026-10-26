"""Marketing mix model: feature building, fitting and decomposition.

Model form (log-linear OLS):
    ln(Volume_t) = b0 + b_weather * weather_t + b_xmas * xmas_t
                 + b_price * ln(relative price_t) + b_dist * distribution_t
                 + sum_c b_c * saturation(adstock(spend_c,t))  + error_t

A log dependent variable makes every effect a % change in volume, so drivers
multiply each other (a hot week lifts media-driven sales too).
"""

from itertools import product

import numpy as np
import pandas as pd
import statsmodels.api as sm

COMPETITORS = ["Comp_Brand_A_", "Comp_Brand_B_", "Comp_Brand_C_"]

# Channels in the final model. VOD and OLV are combined into "Online video":
# both are video formats and they ran in the same weeks, so the model cannot
# separate them. Social is tested but excluded (wrong sign); Search and RDM are
# excluded because they are ~1% of the budget.
MEDIA = {
    "TV": ["Media_TV_Spends"],
    "Online video": ["Media_VOD_Spends", "Media_OLV_Spends"],
    "Online partnership": ["Media_Online_Partnership_Spends"],
    "OOH": ["Media_OOH_Spends"],
}

# Business-sense ranges for the weekly carryover rate of each channel.
# TV and OOH build memory slowly; online partnerships act fast.
ADSTOCK_GRID = {
    "TV": [0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
    "Online video": [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
    "Online partnership": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
    "OOH": [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
    "Social": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
}

HOT_THRESHOLD = 20  # °C - above this, each extra degree adds more sales

BASE_DRIVERS = ["max_temp", "hot_degrees", "rainfall", "xmas_week", "ln_relative_price", "distribution_acv"]

DRIVER_LABELS = {
    "max_temp": "Max temperature (°C)",
    "hot_degrees": f"Degrees above {HOT_THRESHOLD}°C",
    "rainfall": "Rainfall",
    "xmas_week": "Christmas / New Year week",
    "ln_relative_price": "ln(base price / competitor price)",
    "distribution_acv": "Weighted distribution (ACV %)",
}


# ---------------------------------------------------------------- features
def competitor_price(df):
    """Volume-weighted average base price per kg of the three competitors."""
    value = sum(df[f"{p}Volume_Sales"] * df[f"{p}Base_Avg_PPKG"] for p in COMPETITORS)
    volume = sum(df[f"{p}Volume_Sales"] for p in COMPETITORS)
    return value / volume


def base_features(df):
    X = pd.DataFrame(index=df.index)
    X["max_temp"] = df["weather_max_temp"]
    X["hot_degrees"] = np.maximum(df["weather_max_temp"] - HOT_THRESHOLD, 0)
    X["rainfall"] = df["weather_rainfall"]
    month, day = df["Date"].dt.month, df["Date"].dt.day
    X["xmas_week"] = (((month == 12) & (day >= 27)) | ((month == 1) & (day <= 2))).astype(int)
    X["ln_relative_price"] = np.log(df["Base_Avg_PPKG"] / competitor_price(df))
    X["distribution_acv"] = df["ACV_Weighted_Distribution_wtd"]
    return X


def channel_spend(df, channel):
    cols = MEDIA[channel] if channel in MEDIA else [f"Media_{channel}_Spends"]
    return df[cols].sum(axis=1).to_numpy(dtype=float)


def adstock(spend, rate):
    """Geometric carryover: this week's effect = this week's spend + rate * last week's effect."""
    out = np.zeros(len(spend))
    carry = 0.0
    for t, x in enumerate(spend):
        carry = x + rate * carry
        out[t] = carry
    return out


def saturate(adstocked, scale):
    """Diminishing returns: log(1 + x / scale). Doubling spend gives less than double effect."""
    return np.log1p(adstocked / scale)


def saturation_scale(spend, rate):
    """Scale = average adstocked spend in weeks the channel is active (fixed from actual data)."""
    a = adstock(spend, rate)
    return a[a > 0].mean()


def media_features(df, rates, scales=None, spend_override=None):
    """Transformed media variables. spend_override lets us simulate other budgets."""
    X = pd.DataFrame(index=df.index)
    for ch, rate in rates.items():
        spend = channel_spend(df, ch) if spend_override is None else spend_override[ch]
        scale = scales[ch] if scales else saturation_scale(channel_spend(df, ch), rate)
        X[ch] = saturate(adstock(spend, rate), scale)
    return X


# ---------------------------------------------------------------- fitting
def fit_ols(y, X, robust=True):
    """OLS. Robust = Newey-West (HAC) standard errors, which stay honest when
    errors are correlated week to week (common in weekly sales data)."""
    model = sm.OLS(y, sm.add_constant(X))
    if robust:
        return model.fit(cov_type="HAC", cov_kwds={"maxlags": 4})
    return model.fit()


def search_adstock(df, y, X_base, channels, grid=ADSTOCK_GRID):
    """Try every combination of carryover rates; keep the best AIC among models
    where every media coefficient is positive (media cannot reduce sales)."""
    options = {
        ch: {
            r: saturate(adstock(channel_spend(df, ch), r), saturation_scale(channel_spend(df, ch), r))
            for r in grid[ch]
        }
        for ch in channels
    }
    best = None
    for combo in product(*[grid[ch] for ch in channels]):
        X = X_base.copy()
        for ch, r in zip(channels, combo, strict=True):
            X[ch] = options[ch][r]
        res = fit_ols(y, X, robust=False)
        if (res.params[channels] > 0).all() and (best is None or res.aic < best[0]):
            best = (res.aic, dict(zip(channels, combo, strict=True)))
    return None if best is None else best[1]


def mape(actual, predicted):
    return float(np.mean(np.abs(actual - predicted) / actual))


class MMM:
    """Final model: fit once, then predict, decompose and simulate."""

    def __init__(self, df, rates, channels=None):
        self.df = df.reset_index(drop=True)
        self.channels = channels or list(MEDIA)
        self.rates = {ch: rates[ch] for ch in self.channels}
        self.scales = {ch: saturation_scale(channel_spend(self.df, ch), r) for ch, r in self.rates.items()}
        self.X = pd.concat([base_features(self.df), media_features(self.df, self.rates, self.scales)], axis=1)
        self.y = np.log(self.df["Volume_Sales"])
        self.res = fit_ols(self.y, self.X)
        self.params = self.res.params

    def log_predict(self, X):
        return self.params["const"] + X @ self.params[X.columns]

    def predict(self, X=None):
        """Predicted volume (kg). exp() of a log prediction gives the median, so we
        multiply by the smearing factor mean(exp(residual)) to get the mean."""
        X = self.X if X is None else X
        smear = np.mean(np.exp(self.res.resid))
        return np.exp(self.log_predict(X)) * smear

    def with_spend(self, spend):
        """Design matrix with a different weekly spend per channel."""
        X = self.X.copy()
        X[self.channels] = media_features(self.df, self.rates, self.scales, spend_override=spend)
        return X

    def actual_spend(self):
        return {ch: channel_spend(self.df, ch) for ch in self.channels}

    def channel_incremental(self, channel, spend=None, coef=None):
        """Weekly volume that would be lost if this channel were switched off."""
        spend = spend or self.actual_spend()
        X_on = self.with_spend(spend)
        X_off = self.with_spend({**spend, channel: np.zeros(len(self.df))})
        if coef is None:
            return self.predict(X_on) - self.predict(X_off)
        b = self.params.copy()
        b[channel] = coef
        smear = np.mean(np.exp(self.res.resid))
        on = np.exp(b["const"] + X_on @ b[X_on.columns]) * smear
        off = np.exp(b["const"] + X_off @ b[X_off.columns]) * smear
        return on - off

    def decompose(self):
        """Weekly volume split into Base, Weather, Christmas and each media channel.

        Done in steps so the parts add up exactly to predicted volume:
          Base     = cool dry week (coldest observed temperature, no rain), no media,
                     no holiday - at the actual price and distribution of that week
          + Weather  (warmer than the coldest week, hot days, rain; can dip slightly
                     below zero in a cold, very wet week)
          + Christmas week effect
          + Media    (split between channels by each channel's switch-off effect)
        """
        b, X = self.params, self.X
        smear = np.mean(np.exp(self.res.resid))
        t_ref = X["max_temp"].min()

        log_base = (
            b["const"]
            + b["max_temp"] * t_ref
            + b["ln_relative_price"] * X["ln_relative_price"]
            + b["distribution_acv"] * X["distribution_acv"]
        )
        log_weather = (
            b["max_temp"] * (X["max_temp"] - t_ref)
            + b["hot_degrees"] * X["hot_degrees"]
            + b["rainfall"] * X["rainfall"]
        )
        log_xmas = b["xmas_week"] * X["xmas_week"]

        base = np.exp(log_base) * smear
        weather = np.exp(log_base + log_weather) * smear - base
        xmas = np.exp(log_base + log_weather + log_xmas) * smear - base - weather
        total = self.predict()
        media_total = total - base - weather - xmas

        parts = pd.DataFrame({"Base": base, "Weather": weather, "Christmas week": xmas})
        solo = pd.DataFrame({ch: self.channel_incremental(ch) for ch in self.channels})
        share = solo.div(solo.sum(axis=1).replace(0, np.nan), axis=0).fillna(0)
        for ch in self.channels:
            parts[ch] = share[ch] * media_total
        parts.index = self.df["Date"]
        return parts
