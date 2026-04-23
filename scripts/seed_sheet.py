"""Seed the Tatiana Sheet with the tabs and headers the app expects.

Idempotent: re-running updates headers but does not wipe existing data.

Run from project root:
    .venv/Scripts/python.exe scripts/seed_sheet.py
"""
import sys
import tomllib
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

SECRETS_PATH = Path(__file__).resolve().parent.parent / ".streamlit" / "secrets.toml"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

TABS: dict[str, list[str]] = {
    "questions":  ["id", "deck", "text_ru"],
    "answers":    ["id", "timestamp", "card_id", "answer", "asked_adria", "telegram_message_id", "adria_reply", "adria_reply_at"],
    "moods":      ["id", "mood", "text_ru"],
    "mood_seen":  ["mood_id", "seen_at"],
    "reactions":  ["id", "text_ru"],
    "daily_pick": ["date", "card_id"],
    "state":      ["key", "value"],
}

STATE_SEED: list[tuple[str, str]] = [
    ("last_telegram_update_id", "0"),
    ("first_seen_at", ""),
]


def main() -> int:
    with SECRETS_PATH.open("rb") as f:
        secrets = tomllib.load(f)
    creds = Credentials.from_service_account_info(secrets["gcp_service_account"], scopes=SCOPES)
    sheet = gspread.authorize(creds).open_by_key(secrets["SHEET_ID"])

    existing = {ws.title: ws for ws in sheet.worksheets()}

    # Rename the default "Hoja 1" / "Sheet1" to "questions" if present
    if "questions" not in existing:
        default = existing.get("Hoja 1") or existing.get("Sheet1")
        if default is not None:
            default.update_title("questions")
            existing["questions"] = default
            existing.pop("Hoja 1", None)
            existing.pop("Sheet1", None)
            print("Renamed default tab to 'questions'")

    for tab_name, headers in TABS.items():
        if tab_name in existing:
            ws = existing[tab_name]
            print(f"[exists] {tab_name}")
        else:
            ws = sheet.add_worksheet(title=tab_name, rows=100, cols=max(10, len(headers)))
            print(f"[created] {tab_name}")
        ws.update(range_name="A1", values=[headers])

    state_ws = sheet.worksheet("state")
    current_state_keys = {row[0] for row in state_ws.get_all_values()[1:] if row}
    rows_to_append = [[k, v] for k, v in STATE_SEED if k not in current_state_keys]
    if rows_to_append:
        state_ws.append_rows(rows_to_append)
        print(f"Seeded state keys: {[r[0] for r in rows_to_append]}")

    print("\nDone. Final worksheet list:")
    for ws in sheet.worksheets():
        print(f"  - {ws.title}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
