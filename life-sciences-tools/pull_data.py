"""Orchestrates shared/ data pulls for the life-sciences-tools company universe.

Reads config/companies.yaml and, for each company, pulls EDGAR financials
plus relevant alt-data: instrument/reagent order data and biopharma R&D
spend proxies (a leading indicator of tools-company revenue, since tools
vendors sell into biopharma/academic R&D budgets), then persists raw
results for build_signals.py to consume.
"""

from __future__ import annotations

from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "companies.yaml"


def load_companies() -> list[dict]:
    """Load the life-sciences-tools company universe from config/companies.yaml.

    Returns:
        List of company dicts as defined in companies.yaml (ticker, name,
        cik, theme).

    TODO:
        - Parse YAML with pyyaml.
        - Validate required fields are present per entry.
    """
    raise NotImplementedError


def pull_all(companies: list[dict] | None = None) -> None:
    """Run the full data pull (EDGAR + order/spend proxy data) for the given companies.

    Args:
        companies: company dicts to pull for; defaults to load_companies().

    TODO:
        - For each company: shared.edgar.get_quarterly_revenue(cik), plus
          segment data where relevant (many tools names break out
          instruments vs. consumables vs. services).
        - Pull instrument/reagent order data — no public API for this; will
          likely need a new shared/ client wrapping a specific data source
          once one is chosen (e.g. procurement panel, import/export trade
          data for instrument shipments).
        - Pull biopharma R&D spend proxies, e.g. aggregated R&D expense
          across companies tracked in ../biopharma/config, or NIH grant
          award data — no client in shared/ yet.
        - Persist raw pulls (e.g. to outputs/ or a local data/ cache) keyed
          by ticker and source, so build_signals.py doesn't need to re-pull
          on every run.
    """
    raise NotImplementedError


if __name__ == "__main__":
    pull_all()
