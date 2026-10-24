# Frozen research protocol

Written before the benchmark was run, 24 October 2026. This is retrospective research, not a claim of forecasts issued in the past.

## Question

Can a nonlinear quantile model improve native 15-minute DK1/DK2 day-ahead forecasts over a weekly seasonal baseline and standardized ridge regression? Does choosing a flexible load's operating periods using an upper forecast bound reduce realized procurement cost?

## Timeline and information set

- Source: Energinet DayAheadPrices, 1 October 2025 inclusive to 1 October 2026 exclusive, Danish local time. EUR/MWh; native 15-minute delivery periods.
- Decision: 10:00 Europe/Copenhagen on the day before each delivery day. Local days may contain 92, 96 or 100 quarters. Keys and elapsed lags use UTC.
- A price is eligible only after its delivery interval ends plus 24 hours. This conservative research delay is an assumption, not an observed publication timestamp. The archive may contain revisions; this is not a true historical-vintage backtest.
- Features: each zone's price at 72, 96, 168 and 336 elapsed hours before the target; own-zone trailing 24-hour mean/std/min/max ending at the 72-hour lag; known local calendar harmonics and day-of-week flags. Every price feature is checked against the decision cutoff. No realized target-day weather, generation or demand.
- Models update monthly, with the same 120 complete local days of fitting data followed by 28 separate calibration days. The calibration period ends at midnight two days before the month's first delivery day. This leaves all labels available by the model update at 10:00 the previous day. Calibration rows are never fitted.
- Validation deliveries: 1–27 June 2026. Choose the lowest-MAE model separately for each area. Choice is locked before the first July decision; all validation labels have matured. Hyperparameters and decision rules are fixed here, not tuned on validation or test.
- Test deliveries: 1 July–30 September 2026, 92 days. Refit the frozen model recipes on 1 July, 1 August and 1 September using only eligible history. Later refits may use earlier test labels after they become available; this is a rolling operational replay, not one permanently fixed estimator.

## Models and uncertainty

1. Weekly seasonal: price 168 elapsed hours earlier.
2. Ridge: training-only standardization, alpha 10, intercept included.
3. Histogram gradient boosting: quantile losses 0.1/0.5/0.9, 100 iterations, learning rate 0.05, 15 leaves, minimum 80 samples per leaf, L2 1, no early stopping, seed 42.

Independently predicted quantiles are sorted per row to eliminate crossings. Ridge/seasonal use calibration absolute-error intervals. Boosting uses nonnegative calibration scores max(lower−actual, actual−upper, 0), expanding both ends by the finite-sample 80th-percentile score. Nominal marginal coverage is 80%; temporal dependence and regime changes invalidate an exchangeability-based guarantee. Median is unchanged by calibration.

Report MAE, RMSE, signed bias, interval coverage/width, 80% interval score and median pinball loss; compare by month, local delivery hour and negative-price periods. MAE skill is relative to the weekly baseline. No MAPE, since prices can be zero or negative. No test-period model reselection.

## Decision-value experiment

Each area has a separate hypothetical flexible process needing exactly 4 MWh/day, with maximum 1 MW per quarter and no continuity or ramp constraint. It may run in any 16 quarters of the local day. Choose the 16 lowest selected-model median forecasts or upper bounds. Compare realized procurement cost with an evenly spread 4 MWh/day load and a hindsight-only cheapest-quarter lower bound.

Paper orders buy 0.25 MWh each. Assumed execution at the observed day-ahead clearing price plus EUR 0.50/MWh fee, with full fills. Forecast gross budget EUR 1,000/day uses sum(quantity × abs(upper bound)); exceeding it rejects the whole schedule. If rejected, fall back to uniform load so every policy still consumes 4 MWh. Rejection does not guarantee a bound on realized cost. No exchange connection, sell positions, speculative P&L, taxes, grid tariffs or imbalance charges. Shifting may not be physically possible for real assets.

Record PROPOSED, APPROVED, SETTLED, REJECTED and CANCELLED transitions in SQLite; approvals and settlements are atomic and duplicate-resistant. Settlement occurs in replay after the delivery day plus the research data delay. UI phase controls distinguish planned from settled orders.

## Reporting discipline

Publish the frozen recipe, source hashes, fit/calibration windows, selection results and all held-out predictions. Report inferior results and missed coverage. Do not present simulated cost reductions as trading profits or current advice. A separate weather-vintage feature set, market execution and longer regime coverage remain future extensions.
