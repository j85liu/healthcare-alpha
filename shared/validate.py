"""Regression helpers for validating alt-data signals against reported fundamentals.

The core workflow this supports: regress a reported fundamental (e.g.
quarterly revenue) on an alt-data signal (e.g. CMS procedure volume, FDA
clearance cadence), and report enough diagnostics to know whether the fit is
trustworthy rather than a coincidence of two things that both trend upward
over time.

Unlike shared/edgar.py, shared/cms.py, and shared/fda.py, this module is not
a stub — it's implemented now since it has no external API dependency.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.stattools import durbin_watson


# Durbin-Watson stat runs 0-4; ~2.0 means no autocorrelation. Values below
# this threshold (or above 4 - threshold) get flagged as suspect.
DW_AUTOCORRELATION_THRESHOLD = 1.5


@dataclass
class RegressionResult:
    """Diagnostics from a single-variable OLS regression."""

    slope: float
    intercept: float
    r_squared: float
    t_stat: float
    p_value: float
    durbin_watson: float
    high_autocorrelation: bool
    n_obs: int

    def summary(self) -> str:
        flag = " ⚠ HIGH AUTOCORRELATION IN RESIDUALS" if self.high_autocorrelation else ""
        return (
            f"n={self.n_obs}  slope={self.slope:.4g}  intercept={self.intercept:.4g}  "
            f"R²={self.r_squared:.3f}  t={self.t_stat:.2f}  p={self.p_value:.4g}  "
            f"DW={self.durbin_watson:.2f}{flag}"
        )


def run_ols_regression(x: list[float], y: list[float]) -> RegressionResult:
    """Regress y on x with a single-variable OLS fit (LINEST-equivalent).

    Intended use: x = alt-data signal (e.g. procedure volume growth), y =
    reported fundamental (e.g. revenue growth), both aligned to the same
    fiscal periods.

    Args:
        x: independent variable observations.
        y: dependent variable observations, same length and period alignment
            as x.

    Returns:
        RegressionResult with slope, intercept, R², t-stat and p-value on the
        slope coefficient, and a Durbin-Watson autocorrelation check on the
        residuals.

    Raises:
        ValueError: if x and y have fewer than 3 observations or mismatched
            lengths (can't fit a meaningful regression / can't diagnose
            autocorrelation with too few points).

    Note:
        Many of the alt-data and revenue series this will be applied to are
        both trending upward over time (secular growth in robotic surgery
        adoption, for instance). Two unrelated upward-trending series can
        produce a deceptively high R² — that's exactly what the
        Durbin-Watson check is for. A `high_autocorrelation=True` flag means
        "don't trust this R² at face value"; consider differencing the
        series (growth rates instead of levels) before concluding there's a
        real relationship.
    """
    x_arr = np.asarray(x, dtype=float)
    y_arr = np.asarray(y, dtype=float)

    if len(x_arr) != len(y_arr):
        raise ValueError(f"x and y must be the same length (got {len(x_arr)} vs {len(y_arr)})")
    if len(x_arr) < 3:
        raise ValueError("need at least 3 observations to fit and diagnose a regression")

    x_with_const = sm.add_constant(x_arr)
    model = sm.OLS(y_arr, x_with_const).fit()

    dw_stat = durbin_watson(model.resid)
    high_autocorrelation = (
        dw_stat < DW_AUTOCORRELATION_THRESHOLD
        or dw_stat > (4 - DW_AUTOCORRELATION_THRESHOLD)
    )

    return RegressionResult(
        slope=float(model.params[1]),
        intercept=float(model.params[0]),
        r_squared=float(model.rsquared),
        t_stat=float(model.tvalues[1]),
        p_value=float(model.pvalues[1]),
        durbin_watson=float(dw_stat),
        high_autocorrelation=bool(high_autocorrelation),
        n_obs=len(x_arr),
    )


def run_regression(x: list[float], y: list[float]) -> RegressionResult:
    """Generic single-variable OLS regression backtest entry point.

    This is the function callers (medtech/backtest.py and future
    per-ticker/per-subsector backtests) should reach for — it takes no
    ticker- or signal-specific assumptions, just two aligned numeric
    series. It's a thin wrapper around run_ols_regression rather than a
    reimplementation; see that function's docstring for the full
    parameter/return/diagnostic details (R², t-stat, p-value,
    Durbin-Watson autocorrelation flag).

    Args:
        x: independent variable observations (the alt-data signal).
        y: dependent variable observations (the reported fundamental),
            same length and period alignment as x.

    Returns:
        RegressionResult — see run_ols_regression.
    """
    return run_ols_regression(x, y)


def build_clearance_signal(clearances_df: pd.DataFrame, quarters: list[dict]) -> pd.DataFrame:
    """Bucket FDA clearance events into per-quarter counts, aligned to fiscal quarters.

    Produces two features per quarter, both against a fixed quarter
    calendar the caller provides (there's no fiscal-period inference here
    — see medtech/backtest.py for how PRCT's quarters are currently
    defined, since shared/edgar.py doesn't provide real fiscal boundaries
    yet):

        - clearance_count: clearances whose decision_date falls within
          that quarter itself (a contemporaneous count).
        - trailing_2q_count: clearances whose decision_date falls in the
          TWO QUARTERS IMMEDIATELY BEFORE this one (quarters[i-1] and
          quarters[i-2] by list position — NOT including the quarter
          itself). This operationalizes the "clearances lead revenue by
          1-2 quarters" hypothesis without look-ahead bias: it only uses
          clearance activity that had already happened before the quarter
          whose revenue growth you're trying to explain.

    Args:
        clearances_df: DataFrame with at least a `decision_date` column
            (datetime64, or a string pandas can parse) — e.g.
            shared.fda.pull_510k's output, or that CSV read back in with
            decision_date re-parsed to datetime.
        quarters: ordered, contiguous, chronological list of quarter
            dicts, each with "fiscal_period" (a label), "start_date", and
            "end_date" (inclusive bounds; "YYYY-MM-DD" strings or
            datetime-like). Include at least 2 quarters of history before
            the first quarter you actually want a trailing_2q_count for —
            those two lead-in quarters will come back with clearance_count
            filled in but no meaningful trailing_2q_count of their own
            (NaN, since there isn't 2 quarters of history behind them in
            the list you gave).

    Returns:
        DataFrame with columns: fiscal_period, start_date, end_date,
        clearance_count, trailing_2q_count (float, NaN for the first two
        rows — pandas Int64 doesn't mix with NaN as cleanly as float64
        here, and this keeps downstream regression code simple).
    """
    decision_dates = pd.to_datetime(clearances_df["decision_date"])

    rows = []
    for q in quarters:
        start = pd.Timestamp(q["start_date"])
        end = pd.Timestamp(q["end_date"])
        count = int(((decision_dates >= start) & (decision_dates <= end)).sum())
        rows.append(
            {
                "fiscal_period": q["fiscal_period"],
                "start_date": start,
                "end_date": end,
                "clearance_count": count,
            }
        )

    signal_df = pd.DataFrame(rows)
    counts = signal_df["clearance_count"].tolist()

    trailing_2q = [np.nan, np.nan] + [
        counts[i - 1] + counts[i - 2] for i in range(2, len(counts))
    ]
    signal_df["trailing_2q_count"] = trailing_2q

    return signal_df
