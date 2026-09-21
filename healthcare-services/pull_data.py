"""Orchestrates shared/ data pulls for the healthcare-services company universe.

Reads config/companies.yaml and, for each company, pulls EDGAR financials
plus relevant alt-data: CMS utilization data (admissions, visit volumes) and
staffing/labor market data, then persists raw results for build_signals.py
to consume.
"""

from __future__ import annotations

from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "companies.yaml"


def load_companies() -> list[dict]:
    """Load the healthcare-services company universe from config/companies.yaml.

    Returns:
        List of company dicts as defined in companies.yaml (ticker, name,
        cik, theme).

    TODO:
        - Parse YAML with pyyaml.
        - Validate required fields are present per entry.
    """
    raise NotImplementedError


def pull_all(companies: list[dict] | None = None) -> None:
    """Run the full data pull (EDGAR + CMS utilization + staffing/labor) for the given companies.

    Args:
        companies: company dicts to pull for; defaults to load_companies().

    TODO:
        - For each company: shared.edgar.get_quarterly_revenue(cik), plus
          segment data where relevant.
        - Pull CMS utilization data (admissions, ED visits, home health
          episodes) via shared.cms — current shared/cms.py is CPT-procedure
          oriented and will likely need utilization-specific helpers added.
        - Pull staffing/labor data (e.g. BLS healthcare employment series,
          job postings) — no client in shared/ yet; will likely need a new
          shared/labor.py.
        - Persist raw pulls (e.g. to outputs/ or a local data/ cache) keyed
          by ticker and source, so build_signals.py doesn't need to re-pull
          on every run.
    """
    raise NotImplementedError


if __name__ == "__main__":
    pull_all()
