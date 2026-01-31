param(
  [Parameter(Mandatory=$true)]
  [ValidateSet("setup","lint","test","demo","dashboard","weekly","monthly")]
  [string]$Task,

  # Optional override for report anchor date (YYYY-MM-DD).
  # If not provided, we default to a stable demo date so output is deterministic.
  [string]$Today
)

if ($Task -eq "setup") {
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  python -m pip install --upgrade pip
  pip install -r requirements.txt
  pip install -e .
  exit 0
}

if ($Task -eq "lint") {
  ruff format .
  ruff check .
  exit 0
}

if ($Task -eq "test") {
  pytest -v
  exit 0
}

if ($Task -eq "demo") {
  python scripts\paos_run.py all --input data\sample\daily_log.csv --out reports_demo
  exit 0
}

if ($Task -eq "dashboard") {
  python -m streamlit run streamlit_app.py
  exit 0
}

if ($Task -eq "weekly") {
  # Default to a deterministic date for demo runs (previous week lines up with sample data)
  if ([string]::IsNullOrWhiteSpace($Today)) {
    $Today = "2026-01-20"
  }

  python scripts\paos_weekly_report.py `
    --quiet `
    --input-type csv `
    --input data\sample\daily_log.csv `
    --today $Today `
    --out-root reports_demo\weekly `
    --processed-root data\processed\weekly
  exit 0
}

if ($Task -eq "monthly") {
  # Default to a deterministic date for demo runs (month lines up with sample data timeframe)
  if ([string]::IsNullOrWhiteSpace($Today)) {
    $Today = "2026-01-20"
  }

  python scripts\paos_monthly_report.py `
    --input-type csv `
    --input data\sample\daily_log.csv `
    --today $Today `
    --out-root reports_demo\monthly `
    --processed-root data\processed\monthly
  exit 0
}
