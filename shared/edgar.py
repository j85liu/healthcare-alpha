"""SEC EDGAR company facts client.

Pulls quarterly financials (revenue, segment data) from the EDGAR XBRL
"company facts" API:

    https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json

SEC's fair-access rules require a descriptive User-Agent identifying the
requester (name + contact email) on every request, and ask that automated
tools stay under ~10 requests/second. See:
    https://www.sec.gov/os/webmaster-faq#developers
"""

from __future__ import annotations

# TODO: read from env / config instead of hardcoding once the project has a
# real contact. SEC will block requests with a missing or generic UA.
USER_AGENT = "healthcare-alpha research (replace-with-contact@example.com)"

EDGAR_COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"


def fetch_company_facts(cik: str) -> dict:
    """Fetch the full company facts payload for a given CIK.

    Args:
        cik: 10-digit zero-padded SEC Central Index Key (e.g. "0001035267").

    Returns:
        Parsed JSON response from the EDGAR company facts API.

    TODO:
        - Build request with `User-Agent: USER_AGENT` header.
        - GET EDGAR_COMPANY_FACTS_URL.format(cik=cik).
        - Handle 404 (no facts for CIK) and rate limiting.
        - Consider local response caching (EDGAR data updates infrequently
          intraday).
    """
    raise NotImplementedError


def get_quarterly_revenue(cik: str, tag: str = "Revenues") -> list[dict]:
    """Extract quarterly revenue observations from a company's XBRL facts.

    Args:
        cik: 10-digit zero-padded SEC Central Index Key.
        tag: us-gaap XBRL concept to pull (e.g. "Revenues",
            "RevenueFromContractWithCustomerExcludingAssessedTax"). Companies
            are inconsistent about which tag they use, so callers may need
            to try a few.

    Returns:
        List of {"fiscal_year", "fiscal_period", "end_date", "value"} dicts,
        one per reported quarter.

    TODO:
        - Call fetch_company_facts(cik).
        - Walk facts["facts"]["us-gaap"][tag]["units"]["USD"].
        - Filter to form 10-Q / 10-K quarterly entries (fp in {"Q1","Q2","Q3","Q4"}).
        - De-dupe restatements (keep latest filed value per period).
    """
    raise NotImplementedError


def get_segment_revenue(cik: str) -> list[dict]:
    """Extract segment-level revenue breakdowns, where reported.

    Args:
        cik: 10-digit zero-padded SEC Central Index Key.

    Returns:
        List of {"segment", "fiscal_year", "fiscal_period", "end_date",
        "value"} dicts.

    TODO:
        - Segment data isn't always tagged consistently in XBRL; may need to
          look at dimensional/axis members in the raw facts payload, or fall
          back to parsing the 10-Q/10-K segment footnote directly.
    """
    raise NotImplementedError
