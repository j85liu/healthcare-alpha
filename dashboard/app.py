"""Streamlit dashboard: alt-data-implied growth vs. consensus.

For each tracked company, shows the revenue growth implied by its alt-data
signal (per medtech/backtest.py) alongside reported/consensus growth, with
the regression confidence diagnostics surfaced so a divergence can be read
in context rather than taken at face value.

Run with: streamlit run dashboard/app.py
"""

from __future__ import annotations


def load_dashboard_data() -> dict:
    """Load latest backtest results and company metadata for display.

    Returns:
        Dict keyed by ticker with signal-implied growth, reported growth,
        and RegressionResult diagnostics.

    TODO:
        - Pull from medtech.backtest.backtest_all(...) (or a cached
          artifact of it, so the dashboard doesn't re-run pulls on load).
        - Join with config/companies.yaml for display name / theme.
    """
    raise NotImplementedError


def render() -> None:
    """Render the Streamlit dashboard.

    TODO:
        - Table/chart of alt-data-implied growth vs. reported growth per
          ticker, grouped by theme.
        - Surface R², p-value, and the high_autocorrelation flag next to
          each signal so a viewer can't miss a low-confidence read.
        - Link out to outputs/memos/ for the written thesis behind each
          name.
    """
    raise NotImplementedError


if __name__ == "__main__":
    render()
