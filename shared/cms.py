"""CMS (Centers for Medicare & Medicaid Services) procedure-volume client.

Pulls Medicare procedure-volume data by CPT/HCPCS code, used as an alt-data
proxy for procedure adoption trends (e.g. robotic-assisted surgery volumes).
CMS data is public and does not require an API key.

Relevant public datasets to draw from (final source TBD during
implementation):
    - Medicare Physician & Other Practitioners (CPT-level utilization):
      https://data.cms.gov/provider-summary-by-type-of-service/medicare-physician-other-practitioners
    - CMS Data API: https://data.cms.gov/data-api/docs
"""

from __future__ import annotations


def fetch_procedure_volume(cpt_code: str, year: int) -> dict:
    """Fetch national Medicare procedure volume for a given CPT code and year.

    Args:
        cpt_code: 5-digit CPT/HCPCS procedure code (e.g. "55866" for robotic
            prostatectomy).
        year: calendar year of the CMS data release.

    Returns:
        Dict with volume and, where available, geographic/provider breakdowns.

    TODO:
        - Identify the specific CMS dataset/API endpoint per code type.
        - GET request, no auth required.
        - Normalize response into a consistent schema across CMS dataset
          versions (CMS renames/restructures datasets across years).
    """
    raise NotImplementedError


def get_procedure_volume_series(cpt_code: str, start_year: int, end_year: int) -> list[dict]:
    """Fetch a multi-year time series of procedure volume for a CPT code.

    Args:
        cpt_code: 5-digit CPT/HCPCS procedure code.
        start_year: first year (inclusive).
        end_year: last year (inclusive).

    Returns:
        List of {"year", "cpt_code", "volume"} dicts, one per year.

    TODO:
        - Loop fetch_procedure_volume across the year range.
        - CMS typically publishes with a ~1-2 year lag; note data latency
          explicitly when this is wired into signal-building.
    """
    raise NotImplementedError
