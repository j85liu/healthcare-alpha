"""Aligns raw alt-data series to fiscal quarters for each company.

CMS utilization data and staffing/labor series arrive on their own native
calendars (calendar month/quarter, survey release dates), not on each
company's fiscal quarter boundaries. This module resamples/aligns those
series onto each company's actual fiscal quarters (as reported in EDGAR)
so they can be regressed against reported revenue in backtest.py.
"""

from __future__ import annotations


def align_to_fiscal_quarters(raw_series: list[dict], fiscal_periods: list[dict]) -> list[dict]:
    """Align a raw alt-data time series onto a company's fiscal quarter calendar.

    Args:
        raw_series: alt-data observations (e.g. CMS utilization volume by
            month, or staffing/labor observations by month).
        fiscal_periods: the company's fiscal quarter boundaries, as returned
            by shared.edgar.get_quarterly_revenue (end_date per period).

    Returns:
        List of {"fiscal_year", "fiscal_period", "end_date", "value"} dicts,
        one per fiscal quarter, with the alt-data signal bucketed/aggregated
        into that period.

    TODO:
        - Decide aggregation per signal type (sum for utilization volume in
          period, average for staffing/labor levels, etc).
        - Handle fiscal quarters that don't align to calendar quarters.
        - Handle CMS/labor-data reporting lag explicitly (don't silently
          align a not-yet-published period to a quarter that already
          reported).
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
