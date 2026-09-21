"""Orchestrates shared/ data pulls for the managed-care company universe.

Reads config/companies.yaml and, for each company, pulls EDGAR financials
plus relevant alt-data: CMS Medicare Advantage enrollment/plan data and
medical cost ratio proxies (e.g. procedure/utilization volume feeding into
claims costs), then persists raw results for build_signals.py to consume.
"""

from __future__ import annotations

from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "companies.yaml"


def load_companies() -> list[dict]:
    """Load the managed-care company universe from config/companies.yaml.

    Returns:
        List of company dicts as defined in companies.yaml (ticker, name,
        cik, theme).

    TODO:
        - Parse YAML with pyyaml.
        - Validate required fields are present per entry.
    """
    raise NotImplementedError


def pull_all(companies: list[dict] | None = None) -> None:
    """Run the full data pull (EDGAR + CMS Medicare Advantage + MCR proxies) for the given companies.

    Args:
        companies: company dicts to pull for; defaults to load_companies().

    TODO:
        - For each company: shared.edgar.get_quarterly_revenue(cik), plus
          segment data where relevant (health benefits vs. other segments
          for the diversified names).
        - Pull CMS Medicare Advantage enrollment/plan/star-rating data —
          current shared/cms.py is CPT-procedure oriented and will likely
          need MA-specific helpers added (CMS publishes MA enrollment files
          separately from the utilization datasets shared/cms.py targets).
        - Build medical cost ratio proxies from underlying utilization
          trends (can reuse shared.cms procedure-volume data as a claims-
          cost leading indicator once that's wired up).
        - Persist raw pulls (e.g. to outputs/ or a local data/ cache) keyed
          by ticker and source, so build_signals.py doesn't need to re-pull
          on every run.
    """
    raise NotImplementedError


if __name__ == "__main__":
    pull_all()
