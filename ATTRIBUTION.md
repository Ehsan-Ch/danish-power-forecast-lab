# Sources and reuse

**Source: Energinet (www.energidataservice.dk).**

- [DayAheadPrices dataset](https://www.energidataservice.dk/tso-electricity/DayAheadPrices)
- [Dataset metadata](https://api.energidataservice.dk/meta/dataset/DayAheadPrices)
- [API guide](https://www.energidataservice.dk/guides/api-guides): date filters are Danish local time, with end exclusive.
- [Provider terms](https://www.energidataservice.dk/terms-and-conditions): open data under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

The study uses 1 October 2025–1 October 2026, DK1/DK2, TimeUTC and DayAheadPriceEUR. Negative prices are retained. No raw records are interpolated or hourly-aggregated. Features, forecasts, interval estimates, paper decisions and summaries are original transformations. Data-derived reports are distributed under CC BY 4.0 with this attribution; no endorsement by Energinet is implied. Original software is MIT-licensed separately.

Exact request, retrieval timestamp, SHA-256 checksums and software versions are included in `reports/benchmark/results.json`. Raw API responses and source metadata are retained in local ignored `data/` and verified before use. The archive can change; a new download may not match the recorded cache.

Market context: [Nord Pool's transition to 15-minute market time units](https://www.nordpoolgroup.com/en/trading/transition-to-15-minute-market-time-unit-mtu/) and [Nord Pool's DST example](https://www.nordpoolgroup.com/en/trading/Operational-Message-List/2025/10/nord-pool-invites-members-to-dst-test-october-16th-20251009150500/). The 10:00 Copenhagen decision and 24-hour availability delay in this project are research choices, not a complete implementation of exchange rules.

Model implementation: [scikit-learn HistGradientBoostingRegressor](https://scikit-learn.org/1.7/modules/generated/sklearn.ensemble.HistGradientBoostingRegressor.html) and [Ridge](https://scikit-learn.org/1.7/modules/generated/sklearn.linear_model.Ridge.html). Dependencies remain under their respective licenses; no third-party code is vendored into this repository.
