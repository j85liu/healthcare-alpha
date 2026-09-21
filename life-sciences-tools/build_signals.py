"""Aligns raw alt-data series to fiscal quarters for each company.

Order/shipment data and R&D spend proxies arrive on their own native
calendars (survey/panel release schedules, other companies' reporting
dates), not on each company's fiscal quarter boundaries. This module
resamples/aligns those series onto each company's actual fiscal quarters
(as reported in EDGAR) so they can be regressed against reported revenue
in backtest.py.
"""

from __future__ import annotations


def align_to_fiscal_quarters(raw_series: list[dict], fiscal_periods: list[dict]) -> list[dict]:
    """Align a raw alt-data time series onto a company's fiscal quarter calendar.

    Args:
        raw_series: alt-data observations (e.g. instrument order volume by
            month, or aggregated biopharma R&D spend by quarter).
        fiscal_periods: the company's fiscal quarter boundaries, as returned
            by shared.edgar.get_quarterly_revenue (end_date per period).

    Returns:
        List of {"fiscal_year", "fiscal_period", "end_date", "value"} dicts,
        one per fiscal quarter, with the alt-data signal bucketed/aggregated
        into that period.

    TODO:
        - Decide aggregation per signal type (sum for order volume in
          period, average for spend-proxy levels, etc).
        - Handle fiscal quarters that don't align to calendar quarters.
        - R&D spend proxies sourced from other companies' filings (e.g.
          biopharma R&D expense) carry their own reporting lag — don't
          double-count that lag on top of this subsector's own.
    """
    raise NotImplementedError


def build_signal_for_company(ticker: str) -> dict:
    """Build the full set of fiscal-quarter-aligned signals for one company.

    Args:
        ticker: company ticker, matching an entry in config/companies.yaml.

    Returns:
        Dict bundling reported revenue and aligned alt-data signals by
        fiscal quarter, ready for backtest.py.

    TODO:
        - Load raw pulls (from pull_data.py's persisted output).
        - Call align_to_fiscal_quarters for each alt-data series.
        - Join everything on fiscal_year/fiscal_period.
    """
    raise NotImplementedError
