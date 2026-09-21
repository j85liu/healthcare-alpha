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
