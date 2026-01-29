param(
  [Parameter(Mandatory=$true)]
  [ValidateSet("setup","lint","test","demo","dashboard")]
  [string]$Task
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
