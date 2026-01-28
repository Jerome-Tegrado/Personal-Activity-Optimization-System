from __future__ import annotations

import os

DEFAULT_SHEETS_ID: str = os.getenv("PAOS_SHEETS_ID", "").strip()

DEFAULT_SHEETS_RANGE: str = os.getenv(
    "PAOS_SHEETS_RANGE",
    "Form Responses 1!A1:J",
).strip()
