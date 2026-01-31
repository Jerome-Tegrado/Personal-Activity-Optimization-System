# Personal Activity Optimization System (PAOS)
![tests](https://github.com/Jerome-Tegrado/Personal-Activity-Optimization-System/actions/workflows/tests.yml/badge.svg)

PAOS is **my personal analytics system** for turning daily activity logs into decisions I can act on.

It ingests daily logs (CSV or Google Sheets), cleans them, computes an **Activity Level (0–100)**, classifies **Lifestyle Status**, generates **daily recommendations**, produces **interactive + static charts**, and writes **weekly/monthly summaries** I can learn from (and showcase publicly using synthetic data).

> **Privacy-first:** My real personal data stays local (gitignored). This repo ships with **synthetic sample data** that’s safe to commit.

---

## What PAOS does

**Inputs (daily):**
- `date` (required)
- `steps` (required)
- `energy_focus` (1–5, required)
- `did_exercise` (Yes/No, required)
- optional exercise details (type/minutes/zone)
- optional notes (kept private by default)

**Outputs:**
- `step_points` (0–50)
- `exercise_points` (0–50)
- `activity_level` (0–100)
- `lifestyle_status` (Sedentary → Very Active)
- `recommendation` (rule-based, explainable)
- `summary.md` (weekly or monthly)
- charts (Plotly HTML + Matplotlib PNG)

**Optional “v2/v3” features already in this repo:**
- **Google Sheets ingestion** via official API + token caching
- **Weekly + Monthly report wrappers** that stamp outputs into date-based folders
- **Benchmarks (opt-in)**: compare your stats to distribution cutpoints (p25/p50/p75/p90)
- **Experiments (opt-in)**: tag date ranges as control/treatment and compute simple effects
- **Energy prediction (optional)**: train a model and write predictions into a new CSV

---

## Quick demo (safe public data)

Runs the full pipeline on the synthetic sample CSV and writes outputs to `reports_demo/`.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .

# full pipeline: ingest -> transform -> report
python scripts/paos_run.py all --input-type csv --input data/sample/daily_log.csv --out reports_demo

# view outputs
cat reports_demo/summary.md
ls reports_demo/figures/interactive/
ls reports_demo/figures/static/
````

Generated (when figures are enabled):

* `reports_demo/summary.md`
* `reports_demo/figures/interactive/activity_trend.html`
* `reports_demo/figures/interactive/status_counts.html`
* `reports_demo/figures/interactive/activity_vs_energy.html`
* `reports_demo/figures/static/*.png`

> Note: this repo includes `reports_demo/summary.md` and a `.gitkeep`. Figures are generated locally.

---

## CLI: PAOS runner stages (`scripts/paos_run.py`)

The runner is stage-based:

```bash
python scripts/paos_run.py <stage> [options]
```

### Stages

* `all` — ingest → transform → summary + figures
* `ingest` — clean + normalize only (writes to `--processed`)
* `transform` — score/enrich only (writes to `--processed`)
* `report` — build summary + figures from an existing enriched CSV (`--processed`)
* `train-model` — (optional) train an Energy/Focus prediction model
* `predict-energy` — (optional) add predictions into a new CSV

### Common options

* `--input-type {csv,sheets}` (default: `csv`)
* `--input <path>` (CSV only; default is the sample file)
* `--processed <path>` (default: `data/processed/daily_log_enriched.csv`)
* `--out <dir>` (default: `reports`)
* `--no-figures` (skip Plotly/Matplotlib exports for speed / CI stability)

### Example: ingest only

```bash
python scripts/paos_run.py ingest \
  --input-type csv \
  --input data/sample/daily_log.csv \
  --processed data/processed/daily_log_ingested.csv
```

### Example: transform only

```bash
python scripts/paos_run.py transform \
  --input-type csv \
  --input data/sample/daily_log.csv \
  --processed data/processed/daily_log_enriched.csv
```

### Example: report only (from an existing enriched CSV)

```bash
python scripts/paos_run.py report \
  --processed data/processed/daily_log_enriched.csv \
  --out reports_demo
```

---

## Weekly + Monthly reports (stamped folders)

These wrapper scripts run the PAOS runner and automatically write outputs into:

* `reports/weekly/YYYY-Www/`
* `reports/monthly/YYYY-MM/`
  …and processed CSVs into matching folders under `data/processed/...`.

### Weekly

```bash
python scripts/paos_weekly_report.py \
  --input-type csv \
  --input data/sample/daily_log.csv \
  --out-root reports_demo/weekly \
  --processed-root data/processed/weekly
```

### Monthly

```bash
python scripts/paos_monthly_report.py \
  --input-type csv \
  --input data/sample/daily_log.csv \
  --out-root reports_demo/monthly \
  --processed-root data/processed/monthly
```

---

## Dashboard (Streamlit)

`streamlit_app.py` loads an enriched CSV and provides interactive exploration.

1. Generate an enriched CSV:

```bash
python scripts/paos_run.py transform \
  --input-type csv \
  --input data/sample/daily_log.csv \
  --processed data/processed/daily_log_enriched.csv
```

2. Run Streamlit:

```bash
python -m streamlit run streamlit_app.py
```

---

## Google Sheets ingestion (official API)

PAOS supports pulling from a Google Sheet (e.g., Google Forms responses).

### Environment defaults

Create a local `.env` (gitignored). Use `.env.example` as a template:

```bash
PAOS_SHEETS_ID=your_sheet_id_here
PAOS_SHEETS_RANGE=Form Responses 1!A1:J
```

Then run:

```bash
python scripts/paos_run.py all --input-type sheets --out reports
```

### OAuth files (local only)

Sheets ingestion expects these local files (gitignored):

* `secrets/credentials.json`
* `secrets/token.json` (created on first auth)

### Debug: dump a raw Sheets snapshot

```bash
python scripts/paos_run.py all \
  --input-type sheets \
  --dump-raw \
  --raw-out data/processed/sheets_raw.csv \
  --out reports
```

---

## Data model

### Required columns (every day)

| Column         |   Type | Required | Notes                         |
| -------------- | -----: | :------: | ----------------------------- |
| `date`         |   date |     ✅    | primary key (one row per day) |
| `steps`        |    int |     ✅    | daily steps                   |
| `energy_focus` |    int |     ✅    | 1–5 scale                     |
| `did_exercise` | Yes/No |     ✅    | controls exercise scoring     |

### Optional exercise columns (only if you exercised)

| Column             | Type | Required | Notes                               |
| ------------------ | ---: | :------: | ----------------------------------- |
| `exercise_type`    |  str |     ❌    | cardio/strength/mobility/sports     |
| `exercise_minutes` |  int |     ❌    | duration in minutes                 |
| `heart_rate_zone`  |  str |     ❌    | light/moderate/intense/peak/unknown |

### Optional notes (private)

| Column  | Type | Required | Notes                                               |
| ------- | ---: | :------: | --------------------------------------------------- |
| `notes` |  str |     ❌    | optional context; avoid sensitive info if exporting |

### Optional HR columns (supported)

If you have tracker data, PAOS can infer a missing `heart_rate_zone` when `did_exercise` is true.

Supported optional columns (any of these may appear):

* `avg_hr_bpm` (also accepts common variants like `avg_hr`, `average_hr`, etc.)
* `minutes_light`, `minutes_moderate`, `minutes_intense`, `minutes_peak` (also accepts `mins_light`, etc.)

> PAOS will **not overwrite** an existing `heart_rate_zone`. It only fills missing/blank zones when it has enough signal.

### Example CSV (mixed days)

```csv
date,steps,energy_focus,did_exercise,exercise_type,exercise_minutes,heart_rate_zone,notes
2026-01-13,8200,4,Yes,cardio,30,moderate,"Morning jog"
2026-01-14,6500,3,No,,,,"Normal workday"
2026-01-15,10500,5,Yes,strength,45,intense,"Gym session"
2026-01-16,7500,3,No,,,,"Rest day"
```

---

## Scoring logic (explainable by design)

### Step component (0–50)

|       Steps | Points |
| ----------: | -----: |
|     0–4,999 |     10 |
| 5,000–6,999 |     25 |
| 7,000–9,999 |     35 |
|     10,000+ |     50 |

### Exercise component (0–50)

Computed only if `did_exercise` is truthy. Otherwise: `exercise_points = 0`.

**Duration points**

* 0–19 min → 10
* 20–39 min → 25
* 40–60 min → 35
* 61+ min → 45

**Heart rate multipliers**

* light → 0.5×
* moderate → 1.0×
* intense → 1.5×
* peak → 2.0×
* unknown → 1.0×

**Formula**

```text
exercise_points = min(50, int(duration_points * multiplier))
activity_level = step_points + exercise_points
```

### Lifestyle Status

| Activity Level | Status         |
| -------------: | -------------- |
|           0–25 | Sedentary      |
|          26–50 | Lightly Active |
|          51–75 | Active         |
|         76–100 | Very Active    |

---

## Recommendations (rule-based)

* **Sedentary (0–25):** Add a 20–30 min walk.
* **Lightly Active (26–50):** Add a moderate session to reach Active.
* **Active (51–75):** Maintain; add variety (strength/mobility).
* **Very Active (76–100):** Great work; prioritize recovery.

---

## Insights in summaries (privacy-safe)

Weekly/monthly summaries include:

* overview metrics (days logged, averages, status counts)
* Activity ↔ Energy correlation (when valid)
* rule-based insights generated from aggregate patterns

PAOS intentionally keeps this explainable and avoids dumping sensitive raw text.

---

## Benchmarks (optional, public-safe)

You can compare your stats to benchmark distributions using a simple CSV spec.

* Template: `data/benchmarks/benchmarks_template.csv`
* Sample: `data/sample/benchmarks.csv`

Run with:

```bash
python scripts/paos_run.py all \
  --input-type csv \
  --input data/sample/daily_log.csv \
  --benchmarks-spec data/sample/benchmarks.csv \
  --benchmark-group adult \
  --benchmark-metrics steps,activity_level \
  --out reports_demo
```

---

## Experiments (optional)

You can label date ranges as control/treatment to evaluate weekly effects.

* Sample: `data/sample/experiments.csv`

Run with:

```bash
python scripts/paos_run.py all \
  --input-type csv \
  --input data/sample/daily_log.csv \
  --experiments-spec data/sample/experiments.csv \
  --out reports_demo
```

---

## Energy prediction (optional)

PAOS includes an optional ML module that can train a simple model to predict `energy_focus`
from leakage-safe features (lags/rolling means).

### Train

```bash
python scripts/paos_run.py train-model \
  --processed data/processed/daily_log_enriched.csv \
  --model-type ridge \
  --model-path models/energy_model.pkl \
  --out reports_demo
```

### Predict into a new CSV

```bash
python scripts/paos_run.py predict-energy \
  --processed data/processed/daily_log_enriched.csv \
  --model-path models/energy_model.pkl \
  --pred-out data/processed/daily_log_enriched_with_preds.csv
```

Model types:

* `baseline`
* `ridge`
* `rf` (random forest)

---

## Developer commands (Windows / PowerShell)

Helper script: `scripts/dev.ps1`

```powershell
# one-time environment setup
.\scripts\dev.ps1 setup

# format + lint
.\scripts\dev.ps1 lint

# run tests
.\scripts\dev.ps1 test

# demo run (writes to reports_demo/)
.\scripts\dev.ps1 demo

# run dashboard
.\scripts\dev.ps1 dashboard

# weekly + monthly demo outputs (deterministic demo date by default)
.\scripts\dev.ps1 weekly
.\scripts\dev.ps1 monthly

# optional: override anchor date
.\scripts\dev.ps1 weekly -Today "2026-01-20"
```

---

## Tech stack (actual repo)

* Python 3.11+
* pandas, numpy
* Plotly (interactive charts)
* Matplotlib (static charts)
* Streamlit (dashboard)
* Google Sheets API (official client libs)
* pytest (tests)
* ruff (lint + format)
* scikit-learn + joblib (optional energy prediction module)

---

## Project structure (actual repo)

```text
Personal-Activity-Optimization-System-main/
├── .github/workflows/tests.yml
├── .env.example
├── pyproject.toml
├── requirements.txt
├── README.md
├── streamlit_app.py
├── scripts/
│   ├── dev.ps1
│   ├── paos_run.py
│   ├── paos_weekly_report.py
│   ├── paos_monthly_report.py
│   ├── sheets_smoke_test.py
│   └── sheets_to_df_test.py
├── src/paos/
│   ├── config.py
│   ├── ingest/              # CSV + Sheets ingestion (+ optional HR columns normalization)
│   ├── transform/           # scoring, HR zone inference, recommendations
│   ├── viz/                 # Plotly + Matplotlib exports
│   ├── analysis/            # weekly/monthly summaries
│   ├── insights/            # privacy-safe insight generation + redaction helpers
│   ├── experiments/         # experiment assignment + effects
│   ├── benchmarks/          # benchmark comparisons
│   └── machine_learning/    # optional energy model training + prediction
├── data/
│   ├── sample/              # synthetic sample data (safe to commit)
│   └── benchmarks/          # benchmark templates + docs
├── reports_demo/            # public demo outputs (safe to commit)
└── tests/                   # unit tests
```

---

## Testing + CI

Local:

```bash
pytest -v
ruff check .
ruff format .
```

CI (GitHub Actions) runs:

* install deps
* `ruff check .`
* `ruff format --check .`
* `pytest -v`

---

## Privacy & ethics (non-negotiable)

* This is a personal wellness analytics tool, **not medical advice**
* Real personal logs stay in local paths that are **gitignored**
* This repo includes only **synthetic sample data** and **public-safe outputs**
* Notes may contain sensitive context; treat them carefully

---

## Roadmap

* Trend-aware recommendation rules (momentum, recovery flags, weekday patterns)
* More dashboard filters + drilldowns
* Better HR visualizations (time-in-zone charts)
* Experiment framework upgrades (more robust effect metrics)
* Privacy-safe automated insight generation improvements
