# healthcare-alpha

## Thesis

Reported fundamentals lag reality by a quarter or more; alternative data
(procedure volumes, regulatory clearances, and similar leading indicators)
can surface inflection points in adoption trends before they show up in
consensus estimates. This project builds, subsector by subsector, a
pipeline that pulls that alt data, checks it against what companies
actually report, and turns the validated signal into a written investment
thesis — starting with medtech (surgical robotics / procedure-based
devices), where CMS procedure-volume data and FDA clearance activity are
plausible leading indicators of revenue.

## Methodology

1. **Pull alt data** — for each subsector, pull the relevant alternative
   data series (e.g. for medtech: CMS Medicare procedure volumes by CPT
   code, FDA 510(k)/PMA clearance activity) alongside quarterly financials
   from SEC EDGAR.
2. **Validate against reported fundamentals** — align the alt-data series to
   each company's actual fiscal quarters and regress it against reported
   revenue (`shared/validate.py`). This is a deliberate step, not a
   formality: it's where a signal earns the right to be treated as
   predictive rather than coincidental.
3. **Report with explicit confidence caveats** — every regression reports
   R², t-stat, p-value, *and* a Durbin-Watson check on residual
   autocorrelation. Two series that both trend upward over time will
   produce a deceptively high R² with no real relationship; the
   Durbin-Watson flag exists specifically to catch that before it turns
   into a thesis. Written memos (`outputs/memos/`) should carry these
   diagnostics alongside the conclusion, not just the headline number.

## Setup

```bash
# clone, then from the repo root:
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

cp .env.example .env
# edit .env — at minimum, set EDGAR_USER_AGENT to your name + contact email
# (SEC requires this on every EDGAR API request; see .env.example)
```

Run pieces of the pipeline as they get implemented, e.g.:

```bash
python -m medtech.pull_data
streamlit run dashboard/app.py
```

## Project layout

```
config/       ticker/CIK/theme universe per subsector
shared/       API clients (EDGAR, CMS, FDA) and regression/validation helpers
medtech/      medtech-specific pipeline: pull → align → backtest
dashboard/    Streamlit app: alt-data-implied growth vs. consensus
outputs/      dated markdown memos — the written output of the pipeline
```

Data-pulling functions in `shared/` and `medtech/pull_data.py` are
currently stubs (clear docstrings + `TODO`s) — being built out
incrementally. `shared/validate.py` is implemented, since the regression
diagnostics don't depend on any external API.

## Subsectors

- **Medtech (surgical robotics / procedure-based devices)** — in progress.
  Universe: Intuitive Surgical (ISRG), Stryker (SYK), Medtronic (MDT),
  Globus Medical (GMED), Procept BioRobotics (PRCT). See
  `config/companies.yaml`.

  **CMS signal reliability (medtech).** Not every company in this universe
  has a CPT/HCPCS code that cleanly isolates its robotic-assisted procedure
  volume from conventional volume, so `config/companies.yaml`
  (`medtech.companies[].procedure_codes`) and `shared/cms.py`'s module
  docstring rate each ticker's code-based signal on a three-tier scale that
  `medtech/pull_data.py` routes on:

  - **`clean`** — a dedicated, code-isolated procedure code exists and can
    be pulled from CMS claims data as-is. Currently just **PRCT**
    (Aquablation, CPT 0421T — Category III, transitioning to a Category I
    code effective 2026-01-01).
  - **`unverified`** — a plausible isolating code exists but hasn't been
    confirmed against the company's own reimbursement/coding guide yet.
    `pull_data.py` still pulls it, but prints a warning so the resulting
    signal is treated as provisional. Currently **SYK** (Mako) and
    **GMED** (ExcelsiusGPS) — both may have a computer-assisted surgical
    navigation add-on code (e.g. CPT 20985 for musculoskeletal navigation),
    but this needs confirming before it's trusted.
  - **`proxy_only`** — no CPT code isolates the company's robotic
    procedure volume at all; the underlying procedure (e.g. prostatectomy,
    CPT 55866; hysterectomy, CPT 58570-58573) bills identically whether
    performed robotically or via conventional laparoscopy, and the HCPCS
    S2900 robotic-assist add-on isn't Medicare-reimbursed and is used too
    inconsistently to trust for volume tracking. `pull_data.py` skips the
    CMS pull entirely for these and falls back to the company's own
    reported procedure growth % from earnings releases instead. Currently
    **ISRG** (da Vinci) and **MDT** (Hugo).

  Any report or dashboard view built on top of these signals should surface
  which tier backs a given number — an `unverified` or `proxy_only` signal
  is not the same strength of evidence as a `clean` one, and shouldn't be
  presented as if it were.

- **Biopharma** — skeleton in place, not yet built (pull/signal/backtest
  logic still stubs). Alt-data candidates: ClinicalTrials.gov trial
  activity, FDA approvals. Company universe in `config/companies.yaml` is
  filled in: Eli Lilly (LLY), Johnson & Johnson (JNJ), AbbVie (ABBV), Novo
  Nordisk (NVO), AstraZeneca (AZN), Merck (MRK), Pfizer (PFE).
- **Healthcare services** — skeleton in place, not yet built. Alt-data
  candidates: CMS utilization data, staffing/labor data. Company universe
  in `config/companies.yaml` is still placeholder (blank tickers to fill
  in).
- **Life sciences tools** — skeleton in place, not yet built (pull/signal/
  backtest logic still stubs). Alt-data candidates: instrument/reagent
  order data, biopharma R&D spend proxies. Company universe in
  `config/companies.yaml` has Danaher (DHR) filled in, with placeholder
  slots left for more (e.g. Thermo Fisher, Illumina).
- **Managed care** — skeleton in place, not yet built (pull/signal/backtest
  logic still stubs). Alt-data candidates: CMS Medicare Advantage data,
  medical cost ratio proxies. Company universe in `config/companies.yaml`
  has UnitedHealth Group (UNH) filled in, with placeholder slots left for
  more (e.g. Humana, CVS/Aetna).
