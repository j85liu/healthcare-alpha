"""FDA device clearance client.

Pulls 510(k) clearance data from the openFDA device API — used as a leading
indicator of new-product launches ahead of revenue recognition, and
currently the freshest data source in this pipeline (see notes below).

Verified live against the API on 2026-09-22:
    - Endpoint: https://api.fda.gov/device/510k.json — public, keyless, no
      rate-limit tier needed for our volume (standard limit is ~240
      req/min without a key; a free API key registered at
      open.fda.gov/apis/authentication raises that further, and is
      supported here via the OPENFDA_API_KEY env var, but isn't required).
    - Data is fresh: `meta.last_updated` on a live query came back within
      days of the query date, not lagged like the CMS claims dataset (which
      runs ~1-2 years behind). This is our best near-real-time source.
    - Filtering uses Elasticsearch-style query syntax passed as a single
      `search` query param, e.g. `applicant:"company name"`. Build these
      with `requests`' `params=` (never manual string concatenation) so
      quoting/encoding is handled correctly — confirmed this is required
      for the `AND decision_date:[... TO ...]` range syntax to encode
      correctly.
    - Response fields we care about: k_number, applicant, device_name,
      product_code, decision_date, decision_code, decision_description,
      clearance_type.
    - Pagination: capped at limit<=1000 per request (a 400 error above
      that), paged with `skip=`. `skip + limit` beyond roughly 25,000
      total records returns 404 ("No matches found!") rather than an
      error — openFDA's docs describe this as a hard ceiling on skip-based
      paging; going further requires `search_after`, which isn't
      implemented here (see pull_510k's ceiling-warning behavior below).
    - A query with zero matches, or a `skip` past the end of the result
      set, both come back as a 404 with body
      {"error": {"code": "NOT_FOUND", "message": "No matches found!"}} —
      treated as "no more results" rather than a hard failure.

openFDA also has a separate PMA endpoint (api.fda.gov/device/pma.json)
with a different response shape (P-number instead of K-number,
trade_name/generic_name instead of device_name). Not implemented yet —
see get_pma_approvals below.
"""

from __future__ import annotations

import logging
import os
import time

import pandas as pd
import requests

logger = logging.getLogger(__name__)

OPENFDA_510K_URL = "https://api.fda.gov/device/510k.json"
OPENFDA_PMA_URL = "https://api.fda.gov/device/pma.json"

OPENFDA_API_KEY_ENV_VAR = "OPENFDA_API_KEY"  # optional; see .env.example

# openFDA's per-request page cap.
MAX_PAGE_SIZE = 1000
# Observed ceiling on skip + limit for a single query (openFDA returns 404
# past this rather than an error) — paging further requires search_after,
# which this client doesn't implement.
SKIP_CEILING = 25000

REQUEST_TIMEOUT_SECONDS = 15
MAX_RETRIES = 3
RETRY_BACKOFF_BASE_SECONDS = 1.0

_510K_COLUMNS = [
    "k_number",
    "applicant",
    "device_name",
    "product_code",
    "decision_date",
    "decision_type",
    "clearance_type",
]


def _api_key_params() -> dict:
    """Return {"api_key": ...} if OPENFDA_API_KEY is set in the environment, else {}."""
    api_key = os.environ.get(OPENFDA_API_KEY_ENV_VAR)
    return {"api_key": api_key} if api_key else {}


def _build_applicant_query(
    applicant: str,
    decision_date_from: str | None,
    decision_date_to: str | None,
) -> str:
    """Build an openFDA Elasticsearch-style search query for an applicant name, optionally date-bounded."""
    query = f'applicant:"{applicant}"'
    if decision_date_from or decision_date_to:
        lo = decision_date_from or "1900-01-01"
        hi = decision_date_to or "2999-12-31"
        query += f" AND decision_date:[{lo} TO {hi}]"
    return query


def _get_with_retry(url: str, params: dict) -> requests.Response | None:
    """GET url with params, retrying transient failures with exponential backoff.

    Returns:
        The successful Response, or None if the API reports no matches
        (404 with openFDA's "No matches found!" body — this is a normal
        "end of results" signal, not an error, since it's also how openFDA
        reports `skip` past the end of the result set).

    Raises:
        requests.exceptions.RequestException: if retries are exhausted
            without a usable response (network errors, or persistent
            429/5xx responses).
    """
    last_exc: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        except requests.exceptions.RequestException as exc:
            last_exc = exc
            if attempt == MAX_RETRIES:
                raise
            sleep_s = RETRY_BACKOFF_BASE_SECONDS * (2**attempt)
            logger.warning("openFDA request failed (%s); retrying in %.1fs (attempt %d/%d)", exc, sleep_s, attempt + 1, MAX_RETRIES)
            time.sleep(sleep_s)
            continue

        if response.status_code == 404:
            # "No matches found!" — normal end-of-results signal, not a failure.
            return None
        if response.status_code == 429 or response.status_code >= 500:
            if attempt == MAX_RETRIES:
                response.raise_for_status()
            sleep_s = RETRY_BACKOFF_BASE_SECONDS * (2**attempt)
            logger.warning(
                "openFDA returned %d; retrying in %.1fs (attempt %d/%d)",
                response.status_code, sleep_s, attempt + 1, MAX_RETRIES,
            )
            time.sleep(sleep_s)
            continue

        response.raise_for_status()
        return response

    # Unreachable in practice (the loop above always returns or raises on
    # the final attempt), but keeps type checkers happy and fails loudly
    # rather than returning None silently if that assumption ever breaks.
    raise last_exc or RuntimeError("openFDA request failed with no response and no exception")


def _records_to_dataframe(records: list[dict]) -> pd.DataFrame:
    """Normalize raw openFDA 510(k) result records into the standard DataFrame shape."""
    if not records:
        return pd.DataFrame(columns=_510K_COLUMNS)

    rows = [
        {
            "k_number": r.get("k_number"),
            "applicant": r.get("applicant"),
            "device_name": r.get("device_name"),
            "product_code": r.get("product_code"),
            "decision_date": r.get("decision_date"),
            # decision_type is sourced from openFDA's `decision_description`
            # (human-readable, e.g. "Substantially Equivalent") rather than
            # the raw `decision_code` (e.g. "SESE") — more directly useful
            # downstream. The raw code isn't currently kept; add it back as
            # its own column here if a machine-readable code is ever needed.
            "decision_type": r.get("decision_description"),
            "clearance_type": r.get("clearance_type"),
        }
        for r in records
    ]
    df = pd.DataFrame(rows, columns=_510K_COLUMNS)
    df["decision_date"] = pd.to_datetime(df["decision_date"], format="%Y-%m-%d", errors="coerce")
    df = df.sort_values("decision_date", ascending=False, na_position="last").reset_index(drop=True)
    return df


def pull_510k(
    applicant: str,
    decision_date_from: str | None = None,
    decision_date_to: str | None = None,
    limit: int = 100,
) -> pd.DataFrame:
    """Pull 510(k) clearances for a given applicant (company) name from openFDA.

    Args:
        applicant: applicant name as registered with the FDA. Matching is
            openFDA's default full-text search on the `applicant` field —
            case-insensitive and tolerant of partial names in practice
            (e.g. "procept" matches "Procept Biorobotics"), but not a
            guaranteed substring/fuzzy match; see
            config/companies.yaml's fda_applicant_name field and its
            verify-against-real-results caveat.
        decision_date_from: optional "YYYY-MM-DD" lower bound (inclusive)
            on decision_date.
        decision_date_to: optional "YYYY-MM-DD" upper bound (inclusive) on
            decision_date.
        limit: maximum number of records to return, across pages if
            needed (openFDA caps a single page at MAX_PAGE_SIZE=1000).

    Returns:
        DataFrame with columns: k_number, applicant, device_name,
        product_code, decision_date (parsed to datetime64), decision_type,
        clearance_type — sorted by decision_date descending (most recent
        first). Empty (zero-row, same columns) if there are no matches.

    Note:
        If `limit` (or the applicant's total clearance count) would push
        `skip + limit` past SKIP_CEILING (~25,000), results are truncated
        at the ceiling and a warning is logged — this client doesn't
        implement openFDA's `search_after` paging needed to go further.
        In practice no company in this project's universe should have
        anywhere near that many 510(k)s.
    """
    query = _build_applicant_query(applicant, decision_date_from, decision_date_to)

    records: list[dict] = []
    skip = 0
    total: int | None = None

    while len(records) < limit:
        page_size = min(limit - len(records), MAX_PAGE_SIZE)

        if skip + page_size > SKIP_CEILING:
            logger.warning(
                "openFDA 510(k) pull for applicant=%r hit the %d-record skip "
                "ceiling before collecting the requested %d records (%d "
                "collected so far). Results are truncated — this client "
                "doesn't implement search_after-based paging past this "
                "point.",
                applicant, SKIP_CEILING, limit, len(records),
            )
            break

        params = {"search": query, "limit": page_size, "skip": skip}
        params.update(_api_key_params())

        response = _get_with_retry(OPENFDA_510K_URL, params)
        if response is None:
            # No matches at all, or skip has run past the end of the
            # result set — either way, nothing more to collect.
            break

        payload = response.json()
        total = payload.get("meta", {}).get("results", {}).get("total", 0)
        page_records = payload.get("results", [])
        if not page_records:
            break

        records.extend(page_records)
        skip += page_size

        if total is not None and skip >= total:
            break

    return _records_to_dataframe(records[:limit])


def get_pma_approvals(applicant: str, start_date: str | None = None) -> list[dict]:
    """Fetch PMA approvals for a given applicant (company) name.

    Args:
        applicant: company name as registered with the FDA.
        start_date: optional "YYYY-MM-DD" lower bound on decision_date.

    Returns:
        List of approval records (device name, decision date, product code,
        supplement type, etc).

    TODO:
        - Not implemented yet. The PMA endpoint (OPENFDA_PMA_URL) has a
          different response shape than 510(k) — P-number instead of
          K-number, trade_name/generic_name instead of device_name — so
          this needs its own record-normalization logic, not a reuse of
          pull_510k's _records_to_dataframe.
        - Same query/pagination/retry approach as pull_510k should apply
          once implemented (same openFDA API family, same limits).
        - PMA supplements (line extensions) are far more common than new
          originals for established players; decide whether to include them.
    """
    raise NotImplementedError


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    df = pull_510k("procept")
    print(f"\npull_510k('procept') -> {len(df)} clearance(s)\n")
    print(df.head(10).to_string(index=False))
