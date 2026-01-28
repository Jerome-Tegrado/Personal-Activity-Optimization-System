# scripts/sheets_smoke_test.py
from __future__ import annotations

import argparse
import os.path
from typing import List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If you later add write access, you'll update scopes.
SCOPES: List[str] = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_CREDENTIALS_PATH = os.path.join(REPO_ROOT, "secrets", "credentials.json")
DEFAULT_TOKEN_PATH = os.path.join(REPO_ROOT, "secrets", "token.json")


def get_creds(credentials_path: str, token_path: str) -> Credentials:
    creds = None

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            # Opens browser for OAuth consent
            creds = flow.run_local_server(port=0)

        # Save token for next runs
        os.makedirs(os.path.dirname(token_path), exist_ok=True)
        with open(token_path, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

    return creds


def main() -> None:
    parser = argparse.ArgumentParser(description="PAOS Google Sheets API smoke test (read-only).")
    parser.add_argument("--spreadsheet-id", required=True, help="Google Sheet ID (from the URL).")
    parser.add_argument(
        "--range",
        default="Form Responses 1!A1:H10",
        help='A1 notation, e.g. "Form Responses 1!A1:H20" or "Sheet1!A:D".',
    )
    parser.add_argument("--credentials", default=DEFAULT_CREDENTIALS_PATH)
    parser.add_argument("--token", default=DEFAULT_TOKEN_PATH)
    args = parser.parse_args()

    if not os.path.exists(args.credentials):
        raise FileNotFoundError(
            f"Missing credentials file: {args.credentials}\n"
            f"Put your OAuth client JSON at secrets/credentials.json (gitignored)."
        )

    creds = get_creds(args.credentials, args.token)

    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()

    result = sheet.values().get(spreadsheetId=args.spreadsheet_id, range=args.range).execute()
    values = result.get("values", [])

    print("\n=== Sheets Smoke Test ===")
    print(f"Spreadsheet ID: {args.spreadsheet_id}")
    print(f"Range: {args.range}")
    print(f"Rows returned: {len(values)}\n")

    if not values:
        print("No data found in that range.")
        return

    # Print first few rows cleanly
    for i, row in enumerate(values[:10], start=1):
        print(f"Row {i}: {row}")


if __name__ == "__main__":
    main()
