# Model card

**Intended use:** a reproducible portfolio project for Danish power forecasting, quantitative analysis and research-to-decision discussion. Built retrospectively on 24 October 2026.

**Targets:** native 15-minute DK1 and DK2 day-ahead clearing prices in EUR/MWh. No consumer tariff or tax forecast. No live model endpoint.

**Models:** weekly lag baseline; standardized ridge (alpha 10); histogram gradient boosting with quantile loss at 0.1, 0.5 and 0.9. Fixed hyperparameters are in the protocol. Quantiles are sorted if they cross. Ridge is a squared-error point estimator; its center is not claimed to be a statistically fitted median.

**Training and information:** 120 fitting days, 28 separate calibration days, updates at the start of each study month. All price inputs and fitting/calibration labels must be available under a 24-hour-after-delivery-end assumption. Model selection uses June 1–27 only. Subsequent monthly refits can learn from earlier test labels once matured. The pipeline records cutoffs and rejects violations.

**Evaluation:** July 1–September 30, 2026, 8,832 quarter-hours per area. Lower MAE is better; signed bias is forecast minus actual. Interval score penalizes width and misses, at alpha 0.2. No MAPE is used. Scores are descriptive without significance tests or independent winter evaluation.

**Selection risk:** DK1 chooses ridge on validation even though boosting wins the test. DK2 chooses boosting. Deployment selection remains frozen. Inspecting another model in the dashboard does not change paper decision results.

**Uncertainty:** finite-sample residual calibration targets marginal 80% coverage. Temporal dependence and changing price regimes prevent a coverage guarantee. Actual selected-model coverage is 68.2% for DK1 and 73.0% for DK2. This undercoverage is a material limitation. The bands must not be treated as simultaneous daily bounds or a portfolio-risk measure.

**Data limitations:** one year of the quarter-hour dataset; test covers only a summer/autumn window. No weather forecast vintages, load forecasts, renewable forecasts, outages, interconnector availability, fuels or forward curves. The price archive may be revised after publication; hash preservation ensures cache integrity but does not remove vintage bias. The 24-hour delay is intentionally conservative and does not mirror normal day-ahead price availability.

**Decision limitations:** hypothetical freely shiftable 4 MWh/day load; no ramping/continuity requirement, network charges, imbalance cost, capital cost or operational restrictions. Paper orders assume full execution at clearing price plus fixed fee. Forecast-budget approval cannot cap realized costs. No claim of profitable trading, executable bids or production readiness.

**Next justified extension:** collect versioned weather/load/generation forecasts with publication timestamps, test them against the same information boundary, and evaluate across winter and independent later dates before changing model selection. Improve interval reliability through separately validated adaptive calibration rather than tuning on this test set.
