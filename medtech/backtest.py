"""Regresses aligned alt-data signals against reported revenue.

Uses shared.validate.run_ols_regression to test whether an alt-data signal
(procedure volume growth, FDA clearance cadence, etc) has explanatory power
for a company's reported revenue, and reports the confidence diagnostics
needed to avoid over-trusting a spuriously high R² on trending series.
"""

from __future__ import annotations

from shared.validate import RegressionResult


def backtest_signal(ticker: str, signal_name: str) -> RegressionResult:
    """Regress reported revenue growth on an alt-data signal for one company.

    Args:
        ticker: company ticker, matching an entry in config/companies.yaml.
        signal_name: which aligned alt-data signal to test (e.g.
            "cms_procedure_volume", "fda_510k_count").

    Returns:
        RegressionResult from shared.validate.run_ols_regression.

    TODO:
        - Load build_signals.build_signal_for_company(ticker) output.
        - Convert revenue and signal levels to period-over-period growth
          rates (guards against the trending-series false-positive case
          the Durbin-Watson check exists for).
        - Call run_ols_regression(signal_growth, revenue_growth).
        - Consider lagging the signal by one quarter (procedure volume this
          quarter may show up in revenue next quarter, depending on billing
          cycle).
    """
    raise NotImplementedError


def backtest_all(signal_name: str) -> dict[str, RegressionResult]:
    """Run backtest_signal across the full medtech company universe.

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
