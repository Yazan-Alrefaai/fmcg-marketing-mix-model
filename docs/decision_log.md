# Decision log

Every modelling choice, the options considered, the choice made and the evidence behind it.

| # | Decision | Options | Chosen | Why | Evidence |
|---|---|---|---|---|---|
| 1 | KPI (dependent variable) | Volume / Value / Units | Volume_Sales (kg) | Pure demand; price is modelled separately; value mixes in the doubling of price | Value grew while volume fell in 2023 |
| 2 | Weather variable | Avg / max / min temp, rainfall | Max temp (+ hot-week term, rainfall - see 9) | Highest correlation with volume (0.79) | `src/02` output |
| 3 | Distribution variable | Stores selling / ACV max / ACV wtd | ACV wtd | Stores selling rises with demand every summer (endogenous); ACV wtd weights store size | Stores corr 0.51 with temperature, ACV wtd 0.04 |
| 4 | Promotion variable | Promo share / promo depth / promo ACV | Promo ACV wtd tested (final choice: see 11) | Promo share is part of the sales we are explaining; depth unreliable when promo volume is tiny | Promo price > base price in summer 2022 |
| 5 | Competitor variables | Volumes / prices / media | Prices (see 8); media tested (see 20) | Competitor volumes move with the same weather and season (corr 0.76-0.90) | `src/04` output |
| 6 | Holdout period | Random / last weeks | Last 12 weeks | Time series: test on the future, never shuffle | - |
| 7 | Model form | Linear / log-linear / log-log | Log-linear OLS (log of volume), price in logs | Effects are % changes and multiply; price coefficient = elasticity | Adj R² 0.913 |
| 8 | Price variable | Own base price / avg price / relative price | ln(our base price / competitor volume-weighted base price) | All brands' prices rose together (corr 0.83-0.94, inflation); what moves our volume is price vs competitors | Relative price t -6.0 |
| 9 | Weather shape | Linear temp / + hot-week term / thresholds 16-24°C | Max temp + degrees above 20°C + rainfall | Sales accelerate in hot weeks; 18-22°C thresholds fit almost equally, 20°C is easy to explain | AIC within 2 points |
| 10 | Holidays | None / Christmas-New Year dummy | Dummy for week dated 27 Dec - 2 Jan | Same -20% dip every year | t -4.8 |
| 11 | Promotion in model | Promo ACV / depth / promo ACV x depth | None directly; effect measured via distribution | All promo measures t < 1 once distribution is in | `outputs/variables_rejected.csv` |
| 12 | Trend | Include / exclude | Exclude | Collinear with relative price (VIF 12-17); a trend explains nothing to a client | Elasticity -0.46 vs -0.10 with trend (reported as sensitivity) |
| 13 | Media metric | Impressions / spend | Spend | Available for all channels; ROI needs spend; OOH and Online partnership have no impressions | - |
| 14 | VOD + OLV | Separate / combined | Combined "Online video" | Both video, ran in the same weeks (14 of 19 OLV weeks overlap VOD) | Separate: VOD absorbs, OLV negative |
| 15 | Social | Keep / drop | Drop, report "not measurable" | Negative coefficient in every specification | t -1.0 |
| 16 | Search, RDM | Keep / drop | Drop | 1% of budget; cannot be estimated | Search t -2.5 (spurious) |
| 17 | Adstock rates | Fixed / searched | Grid search in business ranges, best AIC with positive signs | Data-driven but within sensible bounds | TV 0.3, video 0.8, OP 0.0, OOH 0.5 |
| 18 | Saturation | None / log / Hill | ln(1 + adstock / scale) | One parameter, easy to explain, concave | - |
| 19 | Standard errors | Plain OLS / HAC | Newey-West HAC (4 lags) | Residual autocorrelation (DW 1.26, Breusch-Godfrey p 0.0002) | `outputs/diagnostics.csv` |
| 20 | Competitor media | Include / exclude | Exclude (report as observation) | Brand A media positive (category halo?) but overlaps our 2024 video campaign | t 2.6 |
| 21 | ROI definition | Revenue / profit | Revenue ROI, using price actually paid | No margin data | - |
