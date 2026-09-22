"""CMS (Centers for Medicare & Medicaid Services) procedure-volume client.

Pulls Medicare procedure-volume data by CPT/HCPCS code, used as an alt-data
proxy for procedure adoption trends (e.g. robotic-assisted surgery volumes).
CMS data is public and does not require an API key.

Relevant public datasets to draw from (final source TBD during
implementation):
    - Medicare Physician & Other Practitioners (CPT-level utilization):
      https://data.cms.gov/provider-summary-by-type-of-service/medicare-physician-other-practitioners
    - CMS Data API: https://data.cms.gov/data-api/docs

CPT-code coverage research (medtech, 2026-09) — why this module takes a
*list* of codes per company rather than assuming one code = one company's
procedure, and why config/companies.yaml carries a `signal_reliability`
rating per ticker:

    - PRCT (Aquablation): has a dedicated, code-isolated procedure — CPT
      0421T (Category III, transitioning to a Category I code effective
      2026-01-01). This is a clean, reliable volume signal pullable
      directly from CMS claims data. -> signal_reliability: "clean"

    - ISRG (da Vinci) and MDT (Hugo): NO dedicated "robotic" CPT code
      exists. Robotic and conventional laparoscopic versions of the same
      procedure (e.g. prostatectomy = CPT 55866, various hysterectomy
      codes 58570-58573) bill under the identical base code. The HCPCS
      add-on S2900 flags robotic assistance but isn't reimbursed by
      Medicare and is inconsistently used, so it isn't reliable for volume
      tracking either. CMS code-based data CANNOT isolate robotic volume
      for these two companies -> signal_reliability: "proxy_only". Use
      company-reported procedure growth % (from earnings releases) as the
      interim proxy instead of a CMS pull; see medtech/pull_data.py.

    - SYK (Mako) and GMED (ExcelsiusGPS): likely have specific
      computer-assisted surgical navigation add-on codes (e.g. CPT 20985
      for musculoskeletal navigation) that may isolate robotic-assisted
      volume more cleanly than ISRG/MDT. This is UNVERIFIED and needs
      confirmation against each company's own reimbursement/coding guide
      before relying on it for a real signal -> signal_reliability:
      "unverified".

See config/companies.yaml (medtech.companies[].procedure_codes) for the
per-ticker cpt_codes / signal_reliability / note values this maps to, and
medtech/pull_data.py for how each reliability tier is routed.
"""

from __future__ import annotations


def fetch_procedure_volume(cpt_code: str, year: int) -> dict:
    """Fetch national Medicare procedure volume for a single CPT/HCPCS code and year.

    Args:
        cpt_code: CPT/HCPCS procedure code (e.g. "0421T" for Aquablation).
            Note: most base procedure codes (e.g. "55866") do NOT isolate
            robotic-assisted volume — see the module docstring above before
            treating a code as a clean per-company signal.
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


def get_procedure_volume_series(
    cpt_codes: list[str], start_year: int, end_year: int
) -> list[dict]:
    """Fetch a multi-year time series of procedure volume across one or more CPT/HCPCS codes.

    Takes a list rather than a single code because a company's alt-data
    signal isn't always a single CPT code: some procedures are billed
    across a small family of related codes (e.g. hysterectomy CPT
    58570-58573), and callers should be able to request the whole family
    and let this function aggregate across it.

    Args:
        cpt_codes: CPT/HCPCS codes to pull and aggregate volume for. Pull
            the reliability-rated code list for a ticker from
            config/companies.yaml (medtech.companies[].procedure_codes)
            rather than hardcoding codes here — see that file and this
            module's docstring for which tickers currently have a
            "clean" vs. "proxy_only" vs. "unverified" code.
        start_year: first year (inclusive).
        end_year: last year (inclusive).

    Returns:
        List of {"year", "cpt_codes", "volume"} dicts, one per year, with
        volume summed across all codes in cpt_codes for that year.

    TODO:
        - Loop fetch_procedure_volume across cpt_codes x the year range.
        - Sum volume per year across codes (decide whether callers ever
          need the per-code breakdown instead of a pre-summed total).
        - CMS typically publishes with a ~1-2 year lag; note data latency
          explicitly when this is wired into signal-building.
        - If cpt_codes is empty (e.g. ISRG/MDT under the current
          proxy_only rating), calling code shouldn't reach this function at
          all — see medtech/pull_data.py's reliability-based routing.
    """
    raise NotImplementedError
