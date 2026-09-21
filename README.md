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
- **Diagnostics / labs** — not started.
- **Pharma / biotech** — not started.
- **Payors / healthcare services** — not started.
