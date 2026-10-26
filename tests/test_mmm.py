"""Tests for data integrity, model maths, results and deliverables.

Run from the project root:  .venv/bin/python -m pytest
"""

import json

import numpy as np
import pandas as pd
import pytest

import mmm
from style import ROOT, load

OUT = ROOT / "outputs"


@pytest.fixture(scope="module")
def df():
    # The data is not part of the repository; tests that need it are skipped without it
    if not (ROOT / "data" / "clean.csv").exists():
        pytest.skip("data not included in the repository (see README)")
    return load()


@pytest.fixture(scope="module")
def model(df):
    rates = json.loads((OUT / "model_config.json").read_text())["rates"]
    return mmm.MMM(df, rates)


# ------------------------------------------------------------------ data
def test_data_is_complete_weekly_series(df):
    assert len(df) == 161
    assert df.isna().sum().sum() == 0
    assert (df["Date"].diff().dropna().dt.days == 7).all()
    assert df["Date"].min() == pd.Timestamp("2022-01-01")


def test_data_definitions_are_consistent(df):
    assert (df["Promotion_Volume_Sales"] <= df["Volume_Sales"]).all()
    assert np.allclose(df["Value_Sales"] / df["Volume_Sales"], df["Avg_PPKG"], atol=0.01)
    assert (df.filter(like="Media_").filter(like="Spends") >= 0).all().all()


def test_clean_csv_matches_raw_excel(df):
    raw = pd.read_excel(ROOT / "data" / "model_variables.xlsx", sheet_name="Model variables")
    assert raw.shape == df.shape
    assert np.allclose(raw["Volume_Sales"], df["Volume_Sales"])


# ------------------------------------------------------------------ transforms
def test_adstock_is_geometric_carryover():
    assert np.allclose(mmm.adstock(np.array([100.0, 0, 0, 0]), 0.5), [100, 50, 25, 12.5])
    assert np.allclose(mmm.adstock(np.array([3.0, 0, 7]), 0.0), [3, 0, 7])


def test_saturation_is_increasing_and_concave():
    x = np.linspace(0, 10, 50)
    s = mmm.saturate(x, scale=2.0)
    assert s[0] == 0
    assert (np.diff(s) > 0).all()
    assert (np.diff(s, 2) < 0).all()


def test_relative_price_uses_volume_weighted_competitors(df):
    cp = mmm.competitor_price(df)
    prices = df[[f"{p}Base_Avg_PPKG" for p in mmm.COMPETITORS]]
    assert ((cp >= prices.min(axis=1) - 1e-9) & (cp <= prices.max(axis=1) + 1e-9)).all()


def test_christmas_flag_marks_one_week_per_year(df):
    flagged = df.loc[mmm.base_features(df)["xmas_week"] == 1, "Date"].dt.strftime("%Y-%m-%d").tolist()
    assert flagged == ["2022-01-01", "2022-12-31", "2023-12-30", "2024-12-28"]


# ------------------------------------------------------------------ model
def test_model_fit_quality(model):
    assert model.res.rsquared_adj > 0.9
    assert mmm.mape(model.df["Volume_Sales"], model.predict()) < 0.05
    assert model.res.nobs == 161


def test_coefficients_have_business_sense_signs(model):
    b = model.params
    assert b["max_temp"] > 0 and b["hot_degrees"] > 0
    assert b["rainfall"] < 0 and b["xmas_week"] < 0
    assert b["ln_relative_price"] < 0
    assert b["distribution_acv"] > 0
    assert all(b[ch] > 0 for ch in model.channels)


def test_core_drivers_are_significant(model):
    for driver in mmm.BASE_DRIVERS:
        assert abs(model.res.tvalues[driver]) > 2, driver


def test_no_harmful_multicollinearity():
    vif = pd.read_csv(OUT / "vif.csv", index_col=0)["VIF"]
    assert (vif < 5).all()


def test_holdout_error_is_close_to_training_error():
    h = pd.read_csv(OUT / "holdout.csv").iloc[0]
    assert h["holdout_MAPE"] < 0.06
    assert abs(h["holdout_bias"]) < 0.05


# ------------------------------------------------------------------ results
def test_decomposition_adds_up_to_prediction(model):
    parts = model.decompose()
    assert np.allclose(parts.sum(axis=1).to_numpy(), model.predict().to_numpy(), rtol=1e-9)
    assert (parts["Base"] > 0).all()
    assert (parts[model.channels] >= -1e-6).all().all()
    assert (parts["Christmas week"] <= 1e-6).all()


def test_switching_off_a_channel_never_adds_sales(model):
    for ch in model.channels:
        inc = model.channel_incremental(ch)
        assert (inc >= -1e-6).all()
        off_weeks = mmm.adstock(mmm.channel_spend(model.df, ch), model.rates[ch]) == 0
        assert np.allclose(inc[off_weeks], 0)


def test_response_curves_show_diminishing_returns(model):
    spend = model.actual_spend()
    price = model.df["Avg_PPKG"].to_numpy()
    for ch in model.channels:
        rev = []
        for k in (1, 2, 3):
            scaled = {**spend, ch: spend[ch] * k}
            rev.append((model.channel_incremental(ch, spend=scaled) * price).sum())
        assert rev[0] < rev[1] < rev[2]
        assert rev[2] - rev[1] < rev[1] - rev[0]


def test_roi_table_matches_model(model):
    media = pd.read_csv(OUT / "media_roi.csv", index_col=0)
    price = model.df["Avg_PPKG"].to_numpy()
    for ch in model.channels:
        roi = (model.channel_incremental(ch) * price).sum() / mmm.channel_spend(model.df, ch).sum()
        assert roi == pytest.approx(media.loc[ch, "roi"], rel=1e-6)
        assert media.loc[ch, "roi_low"] <= media.loc[ch, "roi"] <= media.loc[ch, "roi_high"]


def test_bridge_adds_up_to_actual_change():
    bridge = pd.read_csv(OUT / "volume_bridge.csv", index_col=0)
    parts = bridge.drop("Total (log pts)").sum()
    assert np.allclose(parts, bridge.loc["Total (log pts)"], atol=0.15)


# ------------------------------------------------------------------ deliverables
def test_deck_numbers_match_model_outputs():
    deck = json.loads((ROOT / "deck" / "deck_data.json").read_text())
    media = pd.read_csv(OUT / "media_roi.csv", index_col=0)
    for row in deck["media"]:
        assert row["roi"] == pytest.approx(media.loc[row["channel"], "roi"])
    summary = json.loads((OUT / "results_summary.json").read_text())
    assert deck["share"] == summary["share_of_volume"]


def test_presentation_has_all_slides_and_speaker_notes():
    from pptx import Presentation

    prs = Presentation(ROOT / "MMM_presentation.pptx")
    assert len(prs.slides) == 14
    for i, slide in enumerate(prs.slides, start=1):
        if i == 10:  # appendix divider
            continue
        notes = slide.notes_slide.notes_text_frame.text.strip() if slide.has_notes_slide else ""
        assert notes, f"slide {i} has no notes"
    text = " ".join(sh.text_frame.text for s in prs.slides for sh in s.shapes if sh.has_text_frame)
    for bad in ("undefined", "NaN", "null", "TODO"):
        assert bad not in text


def test_notebook_ran_without_errors():
    import nbformat

    nb = nbformat.read(ROOT / "MMM_analysis.ipynb", as_version=4)
    outputs = [o for c in nb.cells if c.cell_type == "code" for o in c.get("outputs", [])]
    assert not [o for o in outputs if o.output_type == "error"]
    assert not [o for o in outputs if o.output_type == "stream" and o.name == "stderr"]
    assert sum("image/png" in o.get("data", {}) for o in outputs) == 18
