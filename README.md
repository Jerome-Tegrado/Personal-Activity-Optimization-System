# Personal Activity Optimization System (PAOS)
![tests](https://github.com/Jerome-Tegrado/Personal-Activity-Optimization-System/actions/workflows/tests.yml/badge.svg)

PAOS is **my personal analytics system** for turning my daily activity logs into decisions I can act on.

I track **steps + exercise**, compute a **0–100 Activity Level**, classify my **Lifestyle Status**, log my **Energy/Focus (1–5)**, generate **daily recommendations**, and produce **charts + weekly write-ups** I can learn from and also showcase on GitHub.

This is both:
- a real system I’ll use to improve my routines, and
- a portfolio project that proves I can build a complete analytics workflow end-to-end.

---

## My story (why I built this)

I wanted a single place where I can answer questions like:
- “Am I actually becoming more active over time?”
- “Do higher-activity days match higher focus days?”
- “What small changes reliably push me from ‘Lightly Active’ to ‘Active’?”

So I built PAOS to demonstrate a full analytics pipeline:

**data collection → cleaning → feature engineering → analysis → visualization → reporting → iteration**

…and to make it easy for me to run weekly experiments (“lunch walks”, “2 strength sessions/week”, etc.) and measure outcomes.

---

## Demo (60 seconds)

This runs the full pipeline on **synthetic sample data** (safe to commit) and generates charts + a weekly summary.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Generate public demo outputs into reports_demo/
python scripts/paos_run.py all --input-type csv --input data/sample/daily_log.csv --out reports_demo

ls reports_demo/figures/interactive/
ls reports_demo/figures/static/
cat reports_demo/summary.md
````

**What I generate (in the output folder):**

* `figures/interactive/activity_trend.html`
* `figures/interactive/status_counts.html`
* `figures/interactive/activity_vs_energy.html`
* `figures/static/*.png`
* `summary.md`

> My real personal data stays local in `data/raw/` and is never committed.

---

## Developer commands (PowerShell)

If you're on Windows/PowerShell, you can use the helper script:

```powershell
# one-time environment setup
.\scripts\dev.ps1 setup

# format + lint
.\scripts\dev.ps1 lint

# run tests
.\scripts\dev.ps1 test

# run demo on synthetic sample data (writes to reports_demo/)
.\scripts\dev.ps1 demo
```

---

## What I log (inputs)

### Always required (every day)

* **Date**
* **Steps** (from phone/wearable)
* **Energy/Focus** score (1–5)
* **Did you exercise today?** (Yes/No)

### Only if I exercised (optional fields)

* **Exercise Type** (cardio/strength/mobility/sports)
* **Exercise Duration** (minutes)
* **Heart Rate Zone** (light/moderate/intense/peak based on effort)

### Optional any day

* **Notes** (context)

**Important:** On rest days, my **exercise fields can be blank**. Notes can be blank any day.

---

## What PAOS gives me (outputs)

* **Activity Level** score (0–100)
* **Lifestyle Status** category: Sedentary → Lightly Active → Active → Very Active
* **Recommendation text per day**
* Weekly correlation analysis (Activity ↔ Energy/Focus)
* Interactive charts (Plotly) + static backups (Matplotlib)
* A clean report I can share publicly (without private raw data)

---

## The system design (at a glance)

* ✅ One row per day (clean data model)
* ✅ Explainable scoring (0–100)
* ✅ Flexible logging (steps-only OR steps + exercise)
* ✅ Heart rate-based intensity (captures effort, not just duration)
* ✅ Interpretable recommendations (rules first, smarter later)
* ✅ Trend analysis + correlation checks
* ✅ Export-ready output for BI tools
* ✅ Privacy-first repo structure (raw data excluded)

---

## Tech Stack

**Language**

* Python 3.11+

**Data Processing**

* pandas
* numpy
* DuckDB (analytics database)

**Visualization**

* Plotly (interactive charts - primary)
* Matplotlib (static charts - backup)
* Seaborn (optional, notebook EDA)

**Data Sources**

* Google Forms → Google Sheets (my default logging method)
* CSV files (local storage)
* Official Google Sheets API (OAuth + token caching)

**Testing & Quality**

* pytest
* Git/GitHub
* GitHub Actions (CI)

**Dashboard (v2)**

* Streamlit

---

## Project structure

```text
paos/
├── data/
│   ├── raw/                  # my real private inputs (DO NOT COMMIT)
│   ├── processed/            # local enriched outputs (usually DO NOT COMMIT)
│   └── sample/               # synthetic/anonymized examples (OK to commit)
├── notebooks/                # EDA and exploration
├── reports/                  # local reports output (ignored)
├── reports_demo/             # public demo outputs (OK to commit)
│   ├── figures/
│   │   ├── interactive/      # Plotly HTML files
│   │   └── static/           # Matplotlib PNG files
│   └── summary.md            # weekly summary (demo)
├── src/
│   └── paos/
│       ├── config.py         # thresholds + points live here
│       ├── ingest/           # ingestion (CSV, Sheets)
│       ├── transform/        # scoring, classification, recommendations
│       ├── analysis/         # trends, correlations, streaks
│       └── viz/              # chart generation
├── scripts/
│   └── paos_run.py           # pipeline runner
├── tests/
│   └── test_*.py             # unit tests
├── requirements.txt
└── README.md
```

---

## Runner stages (v2)

PAOS supports running smaller parts of the pipeline to debug faster.

### 1) all (default)

Runs ingest → transform → report.

```bash
python scripts/paos_run.py all --input-type csv --input data/sample/daily_log.csv --out reports_demo
```

### 2) ingest

Loads and cleans the input, then writes the ingested CSV to `--processed` (no scoring, no charts).

```bash
python scripts/paos_run.py ingest --input-type csv --input data/sample/daily_log.csv --processed data/processed/daily_log_ingested.csv
```

### 3) transform

Scores/enriches the data and writes the enriched CSV to `--processed` (no charts).

```bash
python scripts/paos_run.py transform --input-type csv --input data/sample/daily_log.csv --processed data/processed/daily_log_enriched.csv
```

### 4) report

Generates `summary.md` + figures from an already-enriched CSV (no ingest, no scoring).

```bash
python scripts/paos_run.py report --processed data/processed/daily_log_enriched.csv --out reports_demo
```

---

## Dashboard (Streamlit)

PAOS includes a simple Streamlit dashboard that loads the enriched CSV and lets you explore your results quickly.

### Run the dashboard

1) Generate an enriched CSV (example using sample data):

```bash
python scripts/paos_run.py transform --input-type csv --input data/sample/daily_log.csv --processed data/processed/daily_log_enriched.csv
```

2) Start Streamlit:

python -m streamlit run streamlit_app.py

---

## Quick start (my real workflow)

1. **Clone**

```bash
git clone <YOUR_REPO_URL>
cd paos
```

2. **Install**

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

3. **Log daily**

* Google Forms → Google Sheets (default)
* or Local CSV (offline)

4. **Run the pipeline (CSV)**

```bash
python scripts/paos_run.py all --input-type csv --input data/raw/daily_log.csv --out reports
```

5. **Run the pipeline (Sheets)**

```bash
python scripts/paos_run.py all --input-type sheets --sheet-id "<YOUR_ID>" --sheet-range "Form Responses 1!A1:J" --out reports
```

> I keep `data/raw/` private and generate local outputs into `reports/` (ignored).
> For GitHub demos, I run against `data/sample/` and output to `reports_demo/`.

---

## Sheets setup (OAuth + env defaults)

PAOS supports environment defaults so you don’t need to pass `--sheet-id` and `--sheet-range` every time.

Create a `.env` file locally (it is gitignored). Use `.env.example` as a template:

```bash
PAOS_SHEETS_ID=your_sheet_id_here
PAOS_SHEETS_RANGE=Form Responses 1!A1:J
```

Then you can run:

```bash
python scripts/paos_run.py all --input-type sheets --out reports
```

### Optional: dump a raw Sheets snapshot (debug)

When Sheets data changes or breaks, you can export the exact raw pull (pre-clean) to a CSV:

```bash
python scripts/paos_run.py all --input-type sheets --dump-raw --raw-out data/processed/sheets_raw.csv --out reports
```

---

## How I log data

### Option A: Google Forms → Google Sheets (default)

I use a Google Form with **conditional sections**, so the exercise fields only appear if I actually exercised.

#### Form structure (sections + question types)

**Section 1 — Daily (Required)**

* **date** → *Date* (Required)
* **steps** → *Short answer* (Required)

  * Validation: number, integer, min 1 (optional max 60000)
* **energy_focus** → *Linear scale 1–5* (Required)
* **did_exercise** → *Multiple choice (Yes/No)* (Required)

  * Turn on **Go to section based on answer**
  * If **Yes** → Section 2
  * If **No** → Section 3

**Section 2 — Exercise Details (Only if you exercised)**
**Description (paste into Google Forms):**

> I fill this section only if I did a dedicated workout today. I enter my main exercise type, total minutes, and effort zone (using my tracker average HR, or the talk test if I don’t have HR data).
> Talk test: sing = light, full sentences = moderate, short phrases = intense, can’t talk = peak.

Questions (all Required in this section):

* **exercise_type** → *Dropdown* (cardio/strength/mobility/sports)
* **exercise_minutes** → *Short answer* (integer minutes)
* **heart_rate_zone** → *Dropdown* (light/moderate/intense/peak/unknown)

**Section 3 — Notes (Optional)**
**Description (paste into Google Forms):**

> I use this for optional context that might explain my activity or energy (e.g., stress, sleep, travel, sickness). I avoid sensitive details if I plan to export/share summaries later.

Question:

* **notes** → *Paragraph* (Optional)

#### Sheets export → PAOS ingestion

Google Forms exports a **Timestamp** column plus my question columns. PAOS cleans it by:

* standardizing column names
* deduplicating by `date` (keep latest submission)
* treating missing exercise fields as **no exercise** for scoring

> My raw form responses keep exercise fields blank on rest days; PAOS only turns that into numeric **exercise_points = 0** during computation.

---

### Option B: Local CSV

I can log either a **minimal CSV** (no exercise columns) or a **full CSV** (mixed days).

**Minimal CSV (steps-only logging)**

```csv
date,steps,energy_focus,did_exercise,notes
2026-01-14,6500,3,No,
2026-01-16,7200,4,No,"Felt good"
```

**Full CSV (mixed days; exercise columns may be blank on rest days)**

```csv
date,steps,energy_focus,did_exercise,exercise_type,exercise_minutes,heart_rate_zone,notes
2026-01-13,8200,4,Yes,cardio,30,moderate,"Morning jog"
2026-01-14,6500,3,No,,,,"Normal workday"
2026-01-15,10500,5,Yes,strength,45,intense,"Gym session"
2026-01-16,7500,3,No,,,,"Rest day"
```

**CSV Rules**

* Always required: `date`, `steps`, `energy_focus`, `did_exercise`
* Optional: `exercise_type`, `exercise_minutes`, `heart_rate_zone`, `notes`
* If `did_exercise = No`, exercise fields can be blank

---

## My personal profile (current)

* Age: **22**
* Height: **5'6"**
* Weight: **70–75 kg**
* Max HR (v1 estimate): **198 bpm** (`220 - age`)

---

## My heart rate zones (PAOS v1)

I use **% of Max HR** bands (with a “talk test” fallback).

Max HR: **198 bpm**

| Zone     | % Max  | HR Range (bpm) | How I tell (talk test)         |
| -------- | ------ | -------------- | ------------------------------ |
| Light    | 50-60% | 99-119         | I can sing comfortably         |
| Moderate | 60-70% | 119-139        | I can talk in full sentences   |
| Intense  | 70-85% | 139-168        | I can only speak short phrases |
| Peak     | 85-95% | 168-188        | I can’t talk, just breathe     |

> If I don’t have a tracker, I choose the zone using the talk test.

---

## Data model

### Raw inputs (what I log)

I store one row per day, and I allow exercise fields to be empty when I don’t exercise.

| Column           | Type     | Required | Example     | Notes                                  |
| ---------------- | -------- | -------- | ----------- | -------------------------------------- |
| date             | date     | ✅        | 2026-01-15  | primary key                            |
| steps            | int      | ✅        | 8123        | total daily steps                      |
| energy_focus     | int      | ✅        | 4           | 1–5 scale                              |
| did_exercise     | bool/str | ✅        | Yes/No      | controls whether exercise fields exist |
| exercise_type    | str      | ❌        | cardio      | blank if no exercise                   |
| exercise_minutes | int      | ❌        | 35          | blank if no exercise                   |
| heart_rate_zone  | str      | ❌        | moderate    | blank if no exercise                   |
| notes            | str      | ❌        | "Deadlines" | optional, sensitive                    |

### Enriched outputs (computed by PAOS)

PAOS generates computed fields for analysis and reporting:

* `step_points`
* `exercise_points` *(computed as 0 if I didn’t exercise)*
* `activity_level` (0–100)
* `lifestyle_status`
* `recommendation`

> Exercise fields can be blank in my raw logs, but PAOS still needs numeric values for scoring.
> So during computation, PAOS treats “no exercise” as **exercise_points = 0** (computed), without requiring me to log “0” in the form.

---

## My scoring logic (explainable on purpose)

### Step component (0–50)

| Steps     | Points |
| --------- | ------ |
| < 5000    | 10     |
| 5000–6999 | 25     |
| 7000–9999 | 35     |
| ≥ 10000   | 50     |

### Exercise component (0–50)

I only compute this if `did_exercise = Yes`. If I didn’t exercise, PAOS computes **exercise_points = 0**.

**Formula**

```text
Exercise Points = base_duration_points × heart_rate_multiplier (max 50)
```

**Duration Points**

* < 20 min: 10 points
* 20–39 min: 25 points
* 40–60 min: 35 points
* > 60 min: 45 points

**Heart Rate Zone Multipliers**

* Light: 0.5x
* Moderate: 1.0x
* Intense: 1.5x
* Peak: 2.0x

Implementation detail:

```text
exercise_points = min(50, int(base_points * multiplier))
```

### Total (0–100)

```text
activity_level = step_points + exercise_points
```

### Lifestyle Status

| Activity Level | Status         |
| -------------- | -------------- |
| 0–25           | Sedentary      |
| 26–50          | Lightly Active |
| 51–75          | Active         |
| 76–100         | Very Active    |

---

## My daily recommendations

Baseline (fast + interpretable):

* **0–25 (Sedentary):** “Add a 20–30 min walk to increase activity and energy.”
* **26–50 (Lightly Active):** “Include a moderate session to reach Active status.”
* **51–75 (Active):** “Maintain routine; add variety (strength/mobility) to avoid plateaus.”
* **76–100 (Very Active):** “Excellent, prioritize recovery (sleep, hydration).”

Trend-aware upgrades I plan (v2):

* Downtrend 3+ days → rebuild momentum plan
* High activity + low energy → recovery check
* Weekday dips → scheduling nudge
* Consecutive sedentary days → motivational nudge

---

## Visualizations

My default set (interactive + static):

1. Activity Level over time
2. Lifestyle Status counts
3. Activity vs Energy/Focus scatter

Outputs (in the chosen output directory):

* Plotly HTML → `figures/interactive/`
* Matplotlib PNG → `figures/static/`

---

## Pipeline contract (what my script does)

```bash
python scripts/paos_run.py all --input-type csv --input <csv_path> --out <output_dir>
```

Outputs:

* `data/processed/daily_log_enriched.csv`
* `<output_dir>/figures/interactive/*.html`
* `<output_dir>/figures/static/*.png`
* `<output_dir>/summary.md`

---

## Testing

Run:

```bash
pytest tests/ -v
```

---

## Privacy & ethics (non-negotiable)

* I treat this as sensitive personal wellness data.
* I don’t publish raw daily logs.
* I commit only synthetic sample data + demo outputs.
* Notes can contain private info; I exclude them from public outputs by default.
* Heart rate data is personal health information; I handle it carefully.
* All personal data stays in `data/raw/` (gitignored).
* This is not medical advice — it’s a personal tracking tool.

---

## Roadmap

### v1 (MVP) - Completed

* ✅ CSV ingestion
* ✅ Flexible logging (exercise fields can be blank)
* ✅ Heart rate zone-based scoring
* ✅ Lifestyle status classification
* ✅ Basic recommendations
* ✅ Export enriched CSV
* ✅ Interactive + static charts
* ✅ Weekly summary generation
* ✅ Unit tests
* ✅ GitHub Actions CI

### v2 (Enhanced) - In progress

* ✅ Google Sheets ingestion via official API
* Streamlit dashboard with filters
* Automated weekly report generator
* Trend-aware recommendations
* HR zone visualization
* Monthly progress reports

### v3 (Advanced)

* Regression model: predict energy from activity + context
* Auto HR zone detection from BPM/time-in-zone
* Privacy-safe automated insight generation
* Experiment tracking framework (A/B test behavior changes)
* Population benchmark comparisons (anonymized)

---

## Installation

```bash
pip install -r requirements.txt
```

---

## Sample Data

This is synthetic sample data (safe to commit).
On rest days, the exercise fields are intentionally blank (because my form skips them):

```csv
date,steps,energy_focus,did_exercise,exercise_type,exercise_minutes,heart_rate_zone,notes
2026-01-13,8200,4,Yes,cardio,30,moderate,"Morning jog"
2026-01-14,6500,3,No,,,,"Normal workday"
2026-01-15,10500,5,Yes,strength,45,intense,"Gym session"
2026-01-16,7500,3,No,,,,"Rest day"
2026-01-17,9200,4,Yes,sports,60,intense,"Basketball with friends"
2026-01-18,5200,2,No,,,,"Busy day, low activity"
2026-01-19,11500,4,Yes,cardio,40,moderate,"Long Sunday walk"
```

---

## License

MIT License.

---

## References

* Google Sheets API (Python quickstart): [https://developers.google.com/workspace/sheets/api/quickstart/python](https://developers.google.com/workspace/sheets/api/quickstart/python)
* DuckDB Python docs: [https://duckdb.org/docs/stable/clients/python/overview](https://duckdb.org/docs/stable/clients/python/overview)
* Plotly Python docs: [https://plotly.com/python/](https://plotly.com/python/)
* Streamlit docs: [https://docs.streamlit.io/](https://docs.streamlit.io/)
* Heart Rate Training Zones basics: [https://www.polar.com/blog/running-heart-rate-zones-basics/](https://www.polar.com/blog/running-heart-rate-zones-basics/)
* pandas docs: [https://pandas.pydata.org/docs/](https://pandas.pydata.org/docs/)
* pytest docs: [https://docs.pytest.org/](https://docs.pytest.org/)
