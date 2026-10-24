# Validation record

Local validation on 24 October 2026.

- 24 Python tests passed: calendar/DST handling, source validation, cutoff checks, future-price mutation, fixed recipes, residual calibration, ledger approvals/rejections/cancellations, duplicate prevention and atomic settlement.
- 5 JavaScript tests passed: report scores match Python, all paper costs reconcile, lifecycle display, negative chart bounds and CSV quoting.
- JavaScript syntax check passed.
- Frozen report: 70,080 source records, 17,664 test targets across both zones and 68,544 model prediction rows including validation. All monthly labels matured before their update cutoff; minimum price-feature availability margin is 9 hours.
- Every paper schedule consumes exactly 4 MWh within the 1 MW limit. Costs reconcile with the order book, including negative-price settlement. All benchmark schedules pass the forecast budget; rejection and cancellation are exercised with synthetic tests.
- Metrics are independently recomputed from published predictions; source-quality zeros mean input validation passed, not that source annotations or market prices were independently audited.

Browser checks passed: DK1/DK2 and date switching, model inspection without changing the frozen policy model, quarter inspection, proposed/approved/settled order views, and a 96-row CSV download checked against report values. No console errors or warnings were observed. A 390-pixel phone viewport showed no page-level horizontal overflow; the desktop chart was also visually inspected.

The tests do not establish live performance, calibration guarantees or real-asset profitability. See the model card and protocol for the information-delay assumption, archive-vintage limitation and physical simplifications.
