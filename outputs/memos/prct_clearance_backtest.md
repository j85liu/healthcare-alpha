# PRCT FDA clearance timing vs. revenue growth — backtest

_Generated 2026-09-23 by medtech/backtest.py._

## Data

- **FDA 510(k)/De Novo clearances:** `outputs/medtech/PRCT_fda_clearances.csv` (via `shared/fda.py`'s `pull_510k`, applicant="PROCEPT BioRobotics"). Tagged by regulatory pathway — the 2017 AQUABEAM grant (DEN170024) was a De Novo classification, not a 510(k); kept in its own `pathway` column rather than pooled with the 510(k) records.
- **PRCT quarterly revenue:** TEMP hardcoded in `medtech/backtest.py` (`shared/edgar.py` is still a stub) — sourced from SEC EDGAR companyfacts (CIK `0001588978`, `us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax`), pulled 2026-09-23. Q4 figures are derived (annual 10-K revenue minus the reported Q1-Q3 quarters), since PRCT's 10-Ks don't report a discrete Q4 figure via XBRL.
- **Quarters used in the regressions:** 2024Q3 through 2026Q2 (**n = 8**).

## Regression results

### (a) Same-quarter clearance count → same-quarter revenue growth

No lead time — tests whether clearance activity simply correlates with growth in the same period.

- n = 8
- slope = -0.01659
- R² = 0.023
- t-stat = -0.38
- p-value = 0.7187
- Durbin-Watson = 2.03

### (b) Trailing-2-quarter clearance count → same-quarter revenue growth

The lag hypothesis: clearances in the two quarters *before* this one (not the current quarter) predicting this quarter's growth — directly testing the README's "new clearances precede revenue contribution by 1-2 quarters" claim.

- n = 8
- slope = 0.02338
- R² = 0.063
- t-stat = 0.64
- p-value = 0.5474
- Durbin-Watson = 2.43

### (c) Naive baseline: prior-quarter revenue growth → same-quarter revenue growth

No alt-data at all — last quarter's growth rate predicting this quarter's. (a) and (b) need to beat this to be worth anything.

- n = 8
- slope = -0.09271
- R² = 0.011
- t-stat = -0.25
- p-value = 0.8091
- Durbin-Watson = 2.06

## Sample size caveat

**n = 8 quarters.** This is below the 10-quarter floor this project treats as a minimum for statistically reliable regression diagnostics — every result above is exploratory, not conclusive. A high R² or low p-value at this sample size can easily come from 1-2 coincidental quarters rather than a real relationship; **don't size a position on this alone.**

## Does clearance timing look like a real leading indicator?

**No clearance-timing signal detected that we'd act on.** trailing-2-quarter clearance count posts the higher of the two alt-data R² values (0.063 vs. baseline 0.011), but n=8 quarters is far too small a sample to call that a real edge rather than noise — with only a handful of data points, a couple of coincidentally well-timed clearances (or one messy quarter, like the Q3→Q4 2025 revenue dip in the data above) can swing R² and the p-value substantially on their own. Honest read: FDA clearance timing has not been *shown* to lead PRCT's revenue growth yet at this sample size. That's a statement about the evidence so far, not a rejection of the underlying hypothesis — it needs more quarters of both clearance and revenue history (ideally n≥10, per this project's own floor) before it's trustworthy either way.

