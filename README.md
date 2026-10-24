# Nordcast · Danish Power Forecast Lab

An auditable **15-minute DK1/DK2 electricity-price forecasting project**, connecting chronological model evaluation to a paper procurement ledger.

**[Open the interactive workbench](https://ehsan-ch.github.io/danish-power-forecast-lab/)** · [Frozen protocol](docs/PROTOCOL.md) · [Model card](docs/MODEL_CARD.md) · [Role relevance](docs/ROLE_RELEVANCE.md) · [Validation](VALIDATION.md)

![Nordcast forecast workbench](reports/preview.jpg)

## What this project demonstrates

- Official Energinet data acquisition, SHA-256 cache checks, strict native-quarter validation and correct Danish clock-change days.
- Forecasts issued at a defined information cutoff, without future-price features or random train/test splits.
- Seasonal, standardized ridge and nonlinear quantile-boosting models, with separate uncertainty calibration.
- Validation-only model choice, monthly refits and an untouched evaluation rule across 92 test days.
- Forecast accuracy, interval coverage, negative-price diagnostics and decision-value analysis.
- An SQLite paper order lifecycle with energy/power limits, budget rejection, cancellation and atomic settlement.
- A public, build-free interactive report and reproducible Python pipeline.

This extends the earlier hourly PowerTrade project with native quarter-hour forecasts, nonlinear conditional intervals, Danish local-day handling and explicit frozen model selection. It is historical research, not an exchange-connected or live forecasting service.

## Main findings

Source window: **1 October 2025–1 October 2026**, end exclusive in Copenhagen time. **70,080 records**, 35,040 per area; no missing or duplicate quarters. Validation: 1–27 June 2026. Test: **1 July–30 September 2026**, 8,832 periods per area.

| Area | Model | Test MAE (EUR/MWh) | Improvement vs weekly | 80% interval coverage |
|---|---|---:|---:|---:|
| DK1 | Weekly seasonal | 49.16 | — | 74.3% |
| DK1 | **Ridge · June-selected** | **45.87** | **6.7%** | **68.2%** |
| DK1 | Quantile boosting | 36.16 | 26.4% | 74.3% |
| DK2 | Weekly seasonal | 47.67 | — | 74.9% |
| DK2 | Ridge | 48.39 | −1.5% | 64.0% |
| DK2 | **Quantile boosting · June-selected** | **36.48** | **23.5%** | **73.0%** |

**The selection does not transfer perfectly:** DK1 selected ridge on June validation, but boosting performs better in the subsequent test. The project retains the June choice instead of silently switching to the test winner. **All interval recipes miss their 80% coverage target** on this test window. September errors rise materially. These findings are part of the result, not hidden exceptions.

## Run

Python 3.11/3.12 and the pinned dependencies:

```sh
python -m venv .venv
# Activate .venv for your operating system, then:
python -m pip install -r requirements.txt
python -m nordcast.cli serve --port 8789
```

Open <http://127.0.0.1:8789/>. The committed report works without downloading data or training. The browser filters locally and uses no third-party scripts, API keys or tracking.

To reproduce from the official source:

```sh
python -m nordcast.cli download --data data
python -m nordcast.cli backtest --data data --out reports/custom/reproduction
```

The source window and evaluation recipe are deliberately fixed. `download` requires a fresh cache directory; `backtest` requires an empty output directory. Neither overwrites an existing study or ledger. Inspect the new result before replacing the demo's `reports/benchmark` files. Raw API data and SQLite files remain local and ignored. Fresh API downloads may contain revisions; match the recorded hashes when comparing results exactly. Small floating-point differences across platforms are possible.

## Forecast design

Each Danish delivery day is forecast at **10:00 Europe/Copenhagen on D−1**. The code handles 92/96/100-quarter days with unique UTC keys. It conservatively treats each historical price as available only 24 hours after the interval ends. That delay is a research assumption; the archive does not establish original publication vintages.

Features use 72/96/168/336-hour price lags in both areas, recent own-area summary statistics and known calendar values. Lags are elapsed UTC hours, including the weekly baseline; around DST this differs from the same local-clock time a week earlier. No realized target-day weather, consumption or generation is used.

For each monthly update, models fit on 120 complete days and calibrate on the following 28 separate days, with a label-maturity gap before issue. Ridge standardization is fitted on training rows only. Quantile boosting estimates 10th/50th/90th percentiles with fixed hyperparameters; residual calibration expands the outer intervals. The full recipe and its hash are in [the protocol](docs/PROTOCOL.md) and the report's provenance. No test-period parameter search is performed.

## Paper procurement experiment

A hypothetical process consumes **4 MWh/day**, at up to **1 MW**. It may operate in any 16 quarters, without continuity or ramp constraints. Compare ranking the selected model's central forecast against ranking its upper bound. The internal policy key `median` means central-forecast ranking; ridge is a squared-error point estimator, not a trained conditional-median model.

| Area | Uniform-load cost | Central-ranking cost | Upper-bound-ranking cost | Hindsight-only lower bound |
|---|---:|---:|---:|---:|
| DK1 | €45,269.18 | €15,862.21 | €15,862.21 | €15,219.47 |
| DK2 | €45,846.19 | €17,336.93 | €17,659.44 | €16,445.54 |

All values cover 92 days and include an assumed €0.50/MWh fee. These large differences rely on freely moving consumption away from expensive quarters; they are **not speculative trading returns**. No tariffs, imbalance charges, asset costs, outages, minimum run lengths or market access are modeled. Full execution is assumed. Hindsight uses future prices and is explicitly not deployable.

The upper-bound rule **does not outperform central ranking in DK2**. In DK1 the calibrated ridge interval has a constant width within each monthly model, so both ranking rules pick the same quarters. Upper-bound ranking is a heuristic, not a guarantee of lower tail cost.

The ledger records `PROPOSED → APPROVED → SETTLED`, plus `REJECTED` and `CANCELLED`. Approval checks a €1,000/day forecast gross budget; rejected schedules fall back to uniform load. All benchmark days pass that budget; rejection and cancellation are tested synthetically. The UI can replay lifecycle phases, rather than suggesting every historical order is still awaiting execution. The ledger is designed for a single-process research run, not a multi-user production ETRM.

## Outputs and checks

- [results.json](reports/benchmark/results.json): daily arrays, metrics, model selections, fit/calibration boundaries, source hashes and versions.
- [predictions.csv.gz](reports/benchmark/predictions.csv.gz): all 68,544 validation/test prediction rows; decompress with standard gzip tools or Python's `gzip` module.
- [orders.csv](reports/benchmark/orders.csv), [batches.csv](reports/benchmark/batches.csv), [events.csv](reports/benchmark/events.csv): paper positions and audit trail.
- `reports/custom/<run>/paper.sqlite`: regenerated local ledger.
- Dashboard export: an ordinary CSV for the area, date and model under inspection.

```sh
python -m unittest discover -s tests -v
node --test tests/test_core.mjs
node --check web/app.js
```

**24 Python tests + 5 JavaScript tests** cover information cutoffs, future-data mutation, DST, calibration, data integrity, ledger lifecycle, independent cost/metric reconstruction and server boundaries. CI runs Python 3.11/3.12 and Node 22. Tests run offline from synthetic cases and committed research outputs; they do not retrain the full benchmark or call the source API.

## Data and license

Source: **Energinet / Energi Data Service**, [DayAheadPrices](https://www.energidataservice.dk/tso-electricity/DayAheadPrices), [official API guide](https://www.energidataservice.dk/guides/api-guides), [terms](https://www.energidataservice.dk/terms-and-conditions). Source data is CC BY 4.0. This project selects DK1/DK2, engineers features, trains models and produces derived analysis; Energinet does not endorse it.

Original code: [MIT](LICENSE). Data-derived research outputs: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), with source attribution retained. See [ATTRIBUTION.md](ATTRIBUTION.md).
