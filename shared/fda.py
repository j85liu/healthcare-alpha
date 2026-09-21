"""FDA device clearance client.

Pulls 510(k) and PMA (Premarket Approval) clearance data, used as a leading
indicator of new-product launches ahead of revenue recognition. Backed by
the openFDA device APIs (public, no key required, but rate-limited more
generously with a free API key):
    - 510(k): https://api.fda.gov/device/510k.json
    - PMA:    https://api.fda.gov/device/pma.json
"""

from __future__ import annotations

OPENFDA_510K_URL = "https://api.fda.gov/device/510k.json"
OPENFDA_PMA_URL = "https://api.fda.gov/device/pma.json"


def get_510k_clearances(applicant: str, start_date: str | None = None) -> list[dict]:
    """Fetch 510(k) clearances for a given applicant (company) name.

    Args:
        applicant: company name as registered with the FDA (matching can be
            inexact; openFDA search may need fuzzy/partial matching).
        start_date: optional "YYYY-MM-DD" lower bound on decision_date.

    Returns:
        List of clearance records (device name, decision date, product code,
        etc).

    TODO:
        - Build openFDA search query against OPENFDA_510K_URL.
        - Handle pagination (openFDA caps at 1000 results per request).
        - Support optional API key via env var for higher rate limits.
    """
    raise NotImplementedError


def get_pma_approvals(applicant: str, start_date: str | None = None) -> list[dict]:
    """Fetch PMA approvals for a given applicant (company) name.

    Args:
        applicant: company name as registered with the FDA.
        start_date: optional "YYYY-MM-DD" lower bound on decision_date.

    Returns:
        List of approval records (device name, decision date, product code,
        supplement type, etc).

    TODO:
        - Same approach as get_510k_clearances, against OPENFDA_PMA_URL.
        - PMA supplements (line extensions) are far more common than new
          originals for established players; decide whether to include them.
    """
    raise NotImplementedError
