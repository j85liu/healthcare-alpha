"""Regresses aligned alt-data signals against reported revenue.

Uses shared.validate.run_ols_regression to test whether an alt-data signal
(Medicare Advantage enrollment, medical cost ratio proxies, etc) has
explanatory power for a company's reported revenue, and reports the
confidence diagnostics needed to avoid over-trusting a spuriously high R²
on trending series.
"""

from __future__ import annotations

from shared.validate import RegressionResult


def backtest_signal(ticker: str, signal_name: str) -> RegressionResult:
    """Regress reported revenue growth on an alt-data signal for one company.

    Args:
        ticker: company ticker, matching an entry in config/companies.yaml.
        signal_name: which aligned alt-data signal to test (e.g.
            "ma_enrollment_growth", "medical_cost_ratio_proxy").

    Returns:
        RegressionResult from shared.validate.run_ols_regression.

    TODO:
        - Load build_signals.build_signal_for_company(ticker) output.
        - Convert revenue and signal levels to period-over-period growth
          rates (guards against the trending-series false-positive case
          the Durbin-Watson check exists for).
        - Call run_ols_regression(signal_growth, revenue_growth).
        - For managed care, medical cost ratio proxies may be more useful
          regressed against reported MCR/earnings than against revenue —
          consider whether backtest_signal needs a second target variable
          when it's implemented.
    """
    raise NotImplementedError


def backtest_all(signal_name: str) -> dict[str, RegressionResult]:
    """Run backtest_signal across the full managed-care company universe.

    Args:
        signal_name: which aligned alt-data signal to test.

    Returns:
        Dict mapping ticker -> RegressionResult.

    TODO:
        - Loop over config/companies.yaml tickers.
        - Skip/log companies with insufficient overlapping history rather
          than failing the whole run.
    """
    raise NotImplementedError


if __name__ == "__main__":
    pass
