"""Smoke test: connect to the Tatiana Sheet via the service account.

Run from project root:
    .venv/Scripts/python.exe scripts/test_sheets.py
"""
import sys
import tomllib
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

SECRETS_PATH = Path(__file__).resolve().parent.parent / ".streamlit" / "secrets.toml"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def main() -> int:
    with SECRETS_PATH.open("rb") as f:
        secrets = tomllib.load(f)

    creds = Credentials.from_service_account_info(
        secrets["gcp_service_account"], scopes=SCOPES
    )
    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(secrets["SHEET_ID"])

    print(f"Connected. Sheet title: {sheet.title!r}")
    print(f"Worksheets: {[ws.title for ws in sheet.worksheets()]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
