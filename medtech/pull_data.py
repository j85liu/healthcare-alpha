"""Orchestrates shared/ data pulls for the medtech company universe.

Reads config/companies.yaml and, for each company, pulls EDGAR financials,
relevant CMS procedure-volume series, and FDA clearance history via the
shared/ clients, then persists raw results for build_signals.py to consume.

CMS pull routing is reliability-gated. Each medtech company's
config/companies.yaml entry carries a procedure_codes.signal_reliability
rating ("clean" | "proxy_only" | "unverified" — see shared/cms.py's module
docstring for the CPT-code research behind each rating). pull_all() only
calls shared.cms for "clean" (PRCT) and "unverified" (SYK, GMED) tickers —
the latter with a printed warning, since those codes haven't been confirmed
against the company's own reimbursement/coding guide yet. "proxy_only"
tickers (ISRG, MDT — no CPT code isolates their robotic procedure volume
from conventional laparoscopic volume) skip the CMS pull entirely and fall
back to a company-reported growth figure instead; see
pull_company_reported_procedure_growth.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from shared import cms

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "companies.yaml"

# CMS claims data is typically published with a ~1-2 year lag behind the
# current year; pull a trailing window that stays clear of not-yet-released
# periods. Revisit once shared.cms is actually implemented and the real
# publication lag per dataset is known.
CMS_REPORTING_LAG_YEARS = 2
CMS_LOOKBACK_YEARS = 5


def load_companies() -> list[dict]:
    """Load the medtech company universe from config/companies.yaml.

    Returns:
        List of company dicts as defined in companies.yaml (ticker, name,
        cik, theme, procedure_codes).

    TODO:
        - Parse YAML with pyyaml.
        - Validate required fields are present per entry, including
          procedure_codes.cpt_codes and procedure_codes.signal_reliability.
    """
    raise NotImplementedError


def pull_company_reported_procedure_growth(company: dict) -> dict:
    """Fetch a company-reported procedure-volume growth figure as a CMS-signal fallback.

    Used for tickers rated "proxy_only" in config/companies.yaml (currently
    ISRG and MDT), where no CPT code isolates robotic-assisted volume from
    conventional laparoscopic volume, so a CMS code-based pull can't
    produce a usable signal for them (see shared/cms.py's module docstring).

    Args:
        company: company dict from load_companies() (at minimum needs
            "ticker" and "name").

    Returns:
        Dict with the company-reported procedure growth figure(s) for the
        period, sourced from the company's own disclosures.

    TODO:
        - This has no API — it needs to come from earnings releases /
          investor presentations (e.g. ISRG discloses da Vinci procedure
          growth % each quarter; MDT discloses Hugo placements/procedures).
          Decide on a source (manual entry into a tracked file? scraped
          from press releases?) before implementing.
        - Persist alongside the CMS-sourced signals in a shape
          build_signals.py can treat consistently, despite the different
          provenance (self-reported vs. CMS claims data) — probably worth
          tagging the record with its source so that distinction isn't
          lost downstream.
    """
    raise NotImplementedError


def pull_all(
    companies: list[dict] | None = None,
    start_year: int | None = None,
    end_year: int | None = None,
) -> None:
    """Run the full data pull (EDGAR + CMS/proxy + FDA) for the given companies.

    Args:
        companies: company dicts to pull for; defaults to load_companies().
        start_year: first year of CMS procedure-volume history to pull;
            defaults to a trailing CMS_LOOKBACK_YEARS window.
        end_year: last year of CMS procedure-volume history to pull;
            defaults to the most recent year CMS data is likely published
            for, given CMS_REPORTING_LAG_YEARS.

    TODO:
        - For each company: shared.edgar.get_quarterly_revenue(cik), plus
          segment data where relevant.
        - Call shared.fda.get_510k_clearances / get_pma_approvals(name).
        - Persist raw pulls (e.g. to outputs/ or a local data/ cache) keyed
          by ticker and source, so build_signals.py doesn't need to re-pull
          on every run.
    """
    if companies is None:
        companies = load_companies()

    if end_year is None:
        end_year = date.today().year - CMS_REPORTING_LAG_YEARS
    if start_year is None:
        start_year = end_year - CMS_LOOKBACK_YEARS

    for company in companies:
        ticker = company["ticker"]
        procedure_codes = company.get("procedure_codes", {})
        reliability = procedure_codes.get("signal_reliability")
        cpt_codes = procedure_codes.get("cpt_codes", [])

        if reliability == "clean":
            cms.get_procedure_volume_series(cpt_codes, start_year, end_year)
        elif reliability == "unverified":
            print(
                f"[pull_data] WARNING: {ticker}'s CPT code(s) {cpt_codes} are "
                "unverified against the company's own reimbursement/coding "
                "guide (see config/companies.yaml note) — treat this signal "
                "as provisional until confirmed."
            )
            cms.get_procedure_volume_series(cpt_codes, start_year, end_year)
        elif reliability == "proxy_only":
            pull_company_reported_procedure_growth(company)
        else:
            print(
                f"[pull_data] WARNING: {ticker} has no recognized "
                f"procedure_codes.signal_reliability rating in "
                "config/companies.yaml — skipping CMS/proxy pull for it."
            )

        # TODO: shared.edgar.get_quarterly_revenue(company["cik"]), plus
        #   segment data where relevant.
        # TODO: shared.fda.get_510k_clearances / get_pma_approvals(company["name"]).

    # TODO: persist raw pulls (e.g. to outputs/ or a local data/ cache) keyed
    #   by ticker and source, so build_signals.py doesn't need to re-pull on
    #   every run.


if __name__ == "__main__":
    pull_all()
