# Connection to Danish energy roles

The exact advertisements previously discussed were not in the available project files. This project therefore uses public employer descriptions as directional references, accessed 24 October 2026; it does not claim to meet every requirement or represent work for those employers.

[Danske Commodities: Quantitative analyst for the Quantitative Weather Analysis team](https://danskecommoditiesas.teamtailor.com/jobs/8517969-quantitative-analyst-for-the-quantitative-weather-analysis-team) describes Python modelling, fundamental forecasting, research and practical support for power trading. [Centrica Energy's careers page](https://centricaenergy.com/career/vacancies/) lists a [Quant Trader for Short-Term Power Trading](https://centrica.wd3.myworkdayjobs.com/Centrica/job/Aalborg/Quant-Trader-for-Short-Term-Power-Trading_R0090842) role in Aalborg/Copenhagen.

| Capability demonstrated | Concrete evidence |
|---|---|
| Reliable data work | Native 15-minute checks, source hashes, timezone-aware delivery keys and DST tests |
| Quantitative research | Three fixed recipes, chronological selection, monthly refits and honest out-of-sample comparisons |
| Uncertainty evaluation | Separate calibration, coverage and interval-score diagnostics, explicit undercoverage finding |
| Practical decision support | Forecast-driven flexible-load scheduling with equal energy across all comparators |
| Engineering discipline | Python package, pinned dependencies, SQLite lifecycle, offline tests and GitHub CI |
| Clear communication | Interactive preview, model card, reproducible protocol and limitations next to the results |

The weather-specialist role also requires weather modelling, which this price-only project does **not** demonstrate. A genuine extension would need archived forecast vintages and evidence that each feature was available at decision time; using realized target-day weather would give an unfair backtest.

## Interview discussion

Explain why the June-selected DK1 model underperforms another model on test without changing the choice after seeing results. Explain why an 80% nominal interval does not achieve 80% coverage under distribution shifts. Demonstrate that mutating future prices cannot change issued features. Show how the quarter-hour energy conversion (MW × 0.25 hours) and negative prices enter paper settlement. Discuss why cost reductions from freely shifting demand are not speculative trading profits.
