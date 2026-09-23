"""Regresses aligned alt-data signals against reported revenue.

First real backtest in this pipeline: tests whether PRCT's FDA 510(k)/De
Novo clearance activity leads its quarterly revenue growth. PRCT is the
first case because it currently has the cleanest data available:
    - A single-entity FDA applicant match ("Procept Biorobotics" / "Procept
      Biorobotics, Corporation" — clearly the same company under minor
      naming variants), unlike e.g. MDT's fda_applicant_name, which pulls
      in unrelated Medtronic subsidiaries (see README's medtech section).
    - A "clean" CMS signal_reliability rating for its CPT 0421T Aquablation
      code (not used in this particular backtest, which is FDA-only, but
      it's the same reason PRCT was picked as the cleanest overall case).
    - A small enough revenue base (~$45-95M/quarter over the window below)
      that a single clearance plausibly moves the needle on
      quarter-over-quarter growth — unlike ISRG, where a single 510(k) is
      a rounding error against >$2B/quarter revenue.

TEMP: PRCT quarterly revenue is hardcoded in PRCT_QUARTERS below rather
than pulled via shared.edgar, which is still a NotImplementedError stub —
same workaround pattern used elsewhere in this pipeline (e.g.
pull_company_reported_procedure_growth in pull_data.py). Values were
pulled directly from SEC EDGAR's companyfacts API
(https://data.sec.gov/api/xbrl/companyfacts/CIK0001588978.json,
us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax) on
2026-09-23. Replace PRCT_QUARTERS with a real
shared.edgar.get_quarterly_revenue("0001588978") call once that's
implemented.

NOTE: while pulling this revenue data, found and fixed a real bug —
config/companies.yaml had PRCT's CIK wrong (0001748790, which actually
resolves to Amcor plc). Corrected to 0001588978; see that file's
CIK-provenance note for detail.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from shared.validate import RegressionResult, build_clearance_signal, run_regression

REPO_ROOT = Path(__file__).resolve().parent.parent
FDA_CLEARANCES_CSV = REPO_ROOT / "outputs" / "medtech" / "PRCT_fda_clearances.csv"
MEMO_PATH = REPO_ROOT / "outputs" / "memos" / "prct_clearance_backtest.md"

# Below this many quarters, treat regression diagnostics as exploratory
# rather than reliable — 8 quarters of data (what we currently have for
# PRCT) does not support strong conclusions from an R²/p-value alone.
MIN_RELIABLE_N = 10

# TEMP hardcoded PRCT quarterly revenue — see module docstring for
# provenance/caveats. Q4 figures are *derived* (annual 10-K revenue minus
# the three reported 10-Q quarters), since PRCT's 10-Ks don't report a
# discrete Q4 figure via XBRL the way the 10-Qs report Q1-Q3 directly:
#   2024Q4 = FY2024 (224,498,000) - Q1 (44,539,000) - Q2 (53,353,000) - Q3 (58,370,000)
#   2025Q4 = FY2025 (308,054,000) - Q1 (69,162,000) - Q2 (79,182,000) - Q3 (83,327,000)
# 2024Q1/Q2 are included only to give 2024Q3+ a revenue-growth base and
# clearance trailing-window history — they aren't themselves part of the
# regressions below (see build_prct_quarterly_table).
PRCT_QUARTERS = [
    {"fiscal_period": "2024Q1", "start_date": "2024-01-01", "end_date": "2024-03-31", "revenue": 44_539_000},
    {"fiscal_period": "2024Q2", "start_date": "2024-04-01", "end_date": "2024-06-30", "revenue": 53_353_000},
    {"fiscal_period": "2024Q3", "start_date": "2024-07-01", "end_date": "2024-09-30", "revenue": 58_370_000},
    {"fiscal_period": "2024Q4", "start_date": "2024-10-01", "end_date": "2024-12-31", "revenue": 68_236_000},
    {"fiscal_period": "2025Q1", "start_date": "2025-01-01", "end_date": "2025-03-31", "revenue": 69_162_000},
    {"fiscal_period": "2025Q2", "start_date": "2025-04-01", "end_date": "2025-06-30", "revenue": 79_182_000},
    {"fiscal_period": "2025Q3", "start_date": "2025-07-01", "end_date": "2025-09-30", "revenue": 83_327_000},
    {"fiscal_period": "2025Q4", "start_date": "2025-10-01", "end_date": "2025-12-31", "revenue": 76_383_000},
    {"fiscal_period": "2026Q1", "start_date": "2026-01-01", "end_date": "2026-03-31", "revenue": 83_132_000},
    {"fiscal_period": "2026Q2", "start_date": "2026-04-01", "end_date": "2026-06-30", "revenue": 94_498_000},
]


def load_fda_clearances(csv_path: Path = FDA_CLEARANCES_CSV) -> pd.DataFrame:
    """Load PRCT's FDA clearance CSV and tag each record with a regulatory pathway.

    Args:
        csv_path: path to the pull_data.py-generated clearances CSV (see
            shared/fda.py, medtech/pull_data.py).

    Returns:
        DataFrame with the original columns from shared.fda.pull_510k's
        output, decision_date parsed to datetime, plus a `pathway` column:
        "de_novo" for De Novo classification records (k_number starting
        with "DEN" — a different regulatory pathway than a 510(k); PRCT's
        original AQUABEAM System, DEN170024, went through De Novo rather
        than a 510(k)), "510k" for everything else. Kept as its own
        column rather than silently pooled with the 510(k) records, since
        a De Novo grant and a 510(k) clearance aren't really the same kind
        of regulatory event.
    """
    df = pd.read_csv(csv_path)
    df["decision_date"] = pd.to_datetime(df["decision_date"])
    df["pathway"] = df["k_number"].apply(lambda k: "de_novo" if str(k).startswith("DEN") else "510k")
    return df


def build_prct_quarterly_table(clearances_df: pd.DataFrame) -> pd.DataFrame:
    """Build the full per-quarter table PRCT's backtest regressions run on.

    Joins build_clearance_signal's per-quarter clearance counts (both
    pathways combined — the trailing-window hypothesis is about clearance
    *activity*, not 510(k)s specifically; see load_fda_clearances if a
    pathway-split signal is ever wanted instead) with the TEMP hardcoded
    revenue levels in PRCT_QUARTERS, and derives revenue growth
    (quarter-over-quarter %) plus a 1-quarter-lagged growth column for the
    naive baseline regression.

    Args:
        clearances_df: output of load_fda_clearances.

    Returns:
        DataFrame with columns: fiscal_period, start_date, end_date,
        revenue, revenue_growth, clearance_count, trailing_2q_count,
        prior_quarter_growth. The first row (2024Q1) has NaN
        revenue_growth (no prior quarter to compute growth from); the
        first two rows have NaN trailing_2q_count (see
        build_clearance_signal) and, consequently, NaN
        prior_quarter_growth for the first two rows as well.
    """
    signal_df = build_clearance_signal(clearances_df, PRCT_QUARTERS)

    revenue_df = pd.DataFrame(PRCT_QUARTERS)[["fiscal_period", "revenue"]]
    table = signal_df.merge(revenue_df, on="fiscal_period", how="left")

    table["revenue_growth"] = table["revenue"].pct_change()
    table["prior_quarter_growth"] = table["revenue_growth"].shift(1)

    return table


def run_backtest() -> dict:
    """Run the three PRCT clearance-vs-revenue-growth regressions and print the results.

    Regressions (all against the same-quarter revenue_growth target):
        (a) same_quarter — same-quarter clearance_count. Tests whether
            clearance activity is simply correlated with growth in the
            same period (no lead time; not really a leading indicator
            even if significant).
        (b) trailing_2q — trailing_2q_count (clearances in the 2 quarters
            BEFORE this one, not including it). Tests the "clearances
            lead revenue by 1-2 quarters" hypothesis from the README
            directly, without look-ahead bias.
        (c) naive_baseline — prior_quarter_growth. A naive autoregressive
            baseline with no alt-data at all: last quarter's growth rate
            predicting this quarter's. (a) and (b) need to beat this R²
            to be worth anything as a signal.

    All three run on the same usable rows: quarters where revenue_growth,
    trailing_2q_count, and prior_quarter_growth are all defined — i.e.
    every PRCT_QUARTERS row except the first two (2024Q1, 2024Q2), which
    exist only to give the later quarters revenue-growth and
    trailing-clearance history.

    Returns:
        Dict with keys "same_quarter", "trailing_2q", "naive_baseline"
        (each a shared.validate.RegressionResult), "table" (the usable
        per-quarter DataFrame), and "n" (sample size).
    """
    clearances_df = load_fda_clearances()
    table = build_prct_quarterly_table(clearances_df)

    usable = table.dropna(
        subset=["revenue_growth", "trailing_2q_count", "prior_quarter_growth"]
    ).reset_index(drop=True)
    n = len(usable)

    print("=" * 78)
    print("PRCT — FDA clearance activity vs. quarterly revenue growth")
    print("=" * 78)
    print()

    pathway_counts = clearances_df["pathway"].value_counts().to_dict()
    print(
        f"Full clearance history loaded: {len(clearances_df)} record(s) "
        f"({pathway_counts.get('510k', 0)} x 510(k), "
        f"{pathway_counts.get('de_novo', 0)} x De Novo) — "
        f"{clearances_df['decision_date'].min().date()} to "
        f"{clearances_df['decision_date'].max().date()}."
    )
    print(
        "Note: only clearances within the regression window below "
        f"({usable['fiscal_period'].iloc[0]}-{usable['fiscal_period'].iloc[-1]}) "
        "feed the regressions; earlier clearances (including the 2017 De "
        "Novo grant) predate the revenue data available and are excluded."
    )
    print()

    print(f"Usable quarters for regression: n={n} ({usable['fiscal_period'].iloc[0]} through {usable['fiscal_period'].iloc[-1]})")
    print()
    print(
        usable[
            [
                "fiscal_period",
                "revenue",
                "revenue_growth",
                "clearance_count",
                "trailing_2q_count",
                "prior_quarter_growth",
            ]
        ].to_string(index=False, formatters={
            "revenue": "${:,.0f}".format,
            "revenue_growth": "{:+.2%}".format,
            "prior_quarter_growth": "{:+.2%}".format,
        })
    )
    print()

    if n < MIN_RELIABLE_N:
        print(
            f"⚠ CAVEAT: n={n} is below the {MIN_RELIABLE_N}-quarter floor this "
            "project treats as a minimum for statistically reliable "
            "regression diagnostics. Every R²/t-stat/p-value below is "
            "exploratory, not conclusive — treat it as a first look, not "
            "a finding. Revisit once more quarters of PRCT revenue and "
            "clearance history are available."
        )
        print()

    same_quarter = run_regression(usable["clearance_count"].tolist(), usable["revenue_growth"].tolist())
    trailing_2q = run_regression(usable["trailing_2q_count"].tolist(), usable["revenue_growth"].tolist())
    naive_baseline = run_regression(usable["prior_quarter_growth"].tolist(), usable["revenue_growth"].tolist())

    print("(a) same-quarter clearance count -> same-quarter revenue growth")
    print(f"    {same_quarter.summary()}")
    print()
    print("(b) trailing-2-quarter clearance count -> same-quarter revenue growth  [lag hypothesis]")
    print(f"    {trailing_2q.summary()}")
    print()
    print("(c) naive baseline: prior-quarter revenue growth -> same-quarter revenue growth")
    print(f"    {naive_baseline.summary()}")
    print()

    print("-" * 78)
    print("Comparison vs. naive baseline (c), by R²")
    print("-" * 78)
    for label, result in [("(a) same-quarter", same_quarter), ("(b) trailing-2q", trailing_2q)]:
        delta = result.r_squared - naive_baseline.r_squared
        verdict = "BEATS" if delta > 0 else "does NOT beat"
        print(
            f"{label}: R²={result.r_squared:.3f}  vs.  baseline R²={naive_baseline.r_squared:.3f}  "
            f"-> {verdict} baseline (Δ={delta:+.3f})"
        )
    print()

    return {
        "same_quarter": same_quarter,
        "trailing_2q": trailing_2q,
        "naive_baseline": naive_baseline,
        "table": usable,
        "n": n,
    }


def write_memo(results: dict, memo_path: Path = MEMO_PATH) -> None:
    """Write a short markdown summary of the backtest to outputs/memos/.

    Args:
        results: dict returned by run_backtest().
        memo_path: where to write the memo (defaults to
            outputs/memos/prct_clearance_backtest.md).

    Writes:
        A markdown file with the three regression results, the n-size
        caveat, and one honest paragraph on whether clearance timing looks
        like a real leading indicator at this sample size — written
        plainly even if the answer is "no signal detected yet."
    """
    same_quarter: RegressionResult = results["same_quarter"]
    trailing_2q: RegressionResult = results["trailing_2q"]
    naive_baseline: RegressionResult = results["naive_baseline"]
    n = results["n"]
    table = results["table"]

    today = date.today().isoformat()

    def fmt(r: RegressionResult) -> str:
        lines = [
            f"- n = {r.n_obs}",
            f"- slope = {r.slope:.4g}",
            f"- R² = {r.r_squared:.3f}",
            f"- t-stat = {r.t_stat:.2f}",
            f"- p-value = {r.p_value:.4g}",
            f"- Durbin-Watson = {r.durbin_watson:.2f}"
            + (" — ⚠ high autocorrelation in residuals" if r.high_autocorrelation else ""),
        ]
        return "\n".join(lines)

    candidates = [
        ("same-quarter clearance count", same_quarter),
        ("trailing-2-quarter clearance count", trailing_2q),
    ]
    best_label, best_result = max(candidates, key=lambda pair: pair[1].r_squared)
    beats_baseline = best_result.r_squared > naive_baseline.r_squared

    if beats_baseline and n >= MIN_RELIABLE_N and best_result.p_value < 0.05:
        conclusion = (
            f"At n={n}, **{best_label}** shows a real, reasonably confident edge "
            "over the naive baseline (R²={:.3f} vs. {:.3f}, p={:.4g}). Worth "
            "tracking forward and re-testing as more quarters accumulate "
            "before sizing a position on it."
        ).format(best_result.r_squared, naive_baseline.r_squared, best_result.p_value)
    else:
        conclusion = (
            f"**No clearance-timing signal detected that we'd act on.** "
            f"{best_label} posts the higher of the two alt-data R² values "
            f"({best_result.r_squared:.3f} vs. baseline {naive_baseline.r_squared:.3f}), "
            f"but n={n} quarters is far too small a sample to call that a real "
            "edge rather than noise — with only a handful of data points, a "
            "couple of coincidentally well-timed clearances (or one messy "
            "quarter, like the Q3→Q4 2025 revenue dip in the data above) can "
            "swing R² and the p-value substantially on their own. Honest "
            "read: FDA clearance timing has not been *shown* to lead PRCT's "
            "revenue growth yet at this sample size. That's a statement "
            "about the evidence so far, not a rejection of the underlying "
            "hypothesis — it needs more quarters of both clearance and "
            "revenue history (ideally n≥10, per this project's own floor) "
            "before it's trustworthy either way."
        )

    lines = [
        "# PRCT FDA clearance timing vs. revenue growth — backtest",
        "",
        f"_Generated {today} by medtech/backtest.py._",
        "",
        "## Data",
        "",
        "- **FDA 510(k)/De Novo clearances:** `outputs/medtech/PRCT_fda_clearances.csv` "
        "(via `shared/fda.py`'s `pull_510k`, applicant=\"PROCEPT BioRobotics\"). "
        "Tagged by regulatory pathway — the 2017 AQUABEAM grant (DEN170024) "
        "was a De Novo classification, not a 510(k); kept in its own "
        "`pathway` column rather than pooled with the 510(k) records.",
        "- **PRCT quarterly revenue:** TEMP hardcoded in `medtech/backtest.py` "
        "(`shared/edgar.py` is still a stub) — sourced from SEC EDGAR "
        "companyfacts (CIK `0001588978`, "
        "`us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax`), "
        f"pulled {today}. Q4 figures are derived (annual 10-K revenue minus "
        "the reported Q1-Q3 quarters), since PRCT's 10-Ks don't report a "
        "discrete Q4 figure via XBRL.",
        f"- **Quarters used in the regressions:** {table['fiscal_period'].iloc[0]} "
        f"through {table['fiscal_period'].iloc[-1]} (**n = {n}**).",
        "",
        "## Regression results",
        "",
        "### (a) Same-quarter clearance count → same-quarter revenue growth",
        "",
        "No lead time — tests whether clearance activity simply correlates "
        "with growth in the same period.",
        "",
        fmt(same_quarter),
        "",
        "### (b) Trailing-2-quarter clearance count → same-quarter revenue growth",
        "",
        "The lag hypothesis: clearances in the two quarters *before* this "
        "one (not the current quarter) predicting this quarter's growth — "
        "directly testing the README's \"new clearances precede revenue "
        "contribution by 1-2 quarters\" claim.",
        "",
        fmt(trailing_2q),
        "",
        "### (c) Naive baseline: prior-quarter revenue growth → same-quarter revenue growth",
        "",
        "No alt-data at all — last quarter's growth rate predicting this "
        "quarter's. (a) and (b) need to beat this to be worth anything.",
        "",
        fmt(naive_baseline),
        "",
        "## Sample size caveat",
        "",
        f"**n = {n} quarters.** " + (
            f"This is below the {MIN_RELIABLE_N}-quarter floor this project "
            "treats as a minimum for statistically reliable regression "
            "diagnostics — every result above is exploratory, not "
            "conclusive. A high R² or low p-value at this sample size can "
            "easily come from 1-2 coincidental quarters rather than a real "
            "relationship; **don't size a position on this alone.**"
            if n < MIN_RELIABLE_N else
            "Meets this project's minimum quarter-count floor, though more "
            "history would still sharpen these estimates."
        ),
        "",
        "## Does clearance timing look like a real leading indicator?",
        "",
        conclusion,
        "",
    ]

    memo_path.parent.mkdir(parents=True, exist_ok=True)
    memo_path.write_text("\n".join(lines) + "\n")
    print(f"Wrote memo to {memo_path}")


if __name__ == "__main__":
    results = run_backtest()
    write_memo(results)
