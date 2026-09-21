"""Orchestrates shared/ data pulls for the medtech company universe.

Reads config/companies.yaml and, for each company, pulls EDGAR financials,
relevant CMS procedure-volume series, and FDA clearance history via the
shared/ clients, then persists raw results for build_signals.py to consume.
"""

from __future__ import annotations

from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "companies.yaml"


def load_companies() -> list[dict]:
    """Load the medtech company universe from config/companies.yaml.

    Returns:
        List of company dicts as defined in companies.yaml (ticker, name,
        cik, theme).

    TODO:
        - Parse YAML with pyyaml.
        - Validate required fields are present per entry.
    """
    raise NotImplementedError


def pull_all(companies: list[dict] | None = None) -> None:
    """Run the full data pull (EDGAR + CMS + FDA) for the given companies.

    Args:
        companies: company dicts to pull for; defaults to load_companies().

    TODO:
        - For each company: shared.edgar.get_quarterly_revenue(cik), plus
          segment data where relevant.
        - Map each company's theme to relevant CPT codes and call
          shared.cms.get_procedure_volume_series(...).
        - Call shared.fda.get_510k_clearances / get_pma_approvals(name).
        - Persist raw pulls (e.g. to outputs/ or a local data/ cache) keyed
          by ticker and source, so build_signals.py doesn't need to re-pull
          on every run.
    """
    raise NotImplementedError


if __name__ == "__main__":
    pull_all()
