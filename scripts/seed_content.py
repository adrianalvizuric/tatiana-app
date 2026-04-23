"""Seed question decks and scripted reactions into the Sheet.

Mood messages are NOT seeded here — Adria writes them directly in the
`moods` tab (columns: id, mood, text_ru). Recommended IDs: miss_1..miss_5,
cant_sleep_1..cant_sleep_5.

Idempotent: rows whose `id` already exists are skipped.

Run from project root:
    .venv/Scripts/python.exe scripts/seed_content.py
"""
import sys
import tomllib
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

SECRETS_PATH = Path(__file__).resolve().parent.parent / ".streamlit" / "secrets.toml"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


FLIRTY: list[str] = [
    "Что я делаю, что сводит тебя с ума (в хорошем смысле)?",
    "Какое моё сообщение ты перечитываешь чаще всего?",
    "Опиши нашу первую встречу так, как будто рассказываешь её подруге.",
    "Что бы ты сделала со мной, если бы я был рядом прямо сейчас?",
    "Какая часть моего тела твоя любимая и почему?",
    "Что мне надеть в нашу следующую встречу?",
    "Какой твой самый смелый секрет про меня?",
    "Когда ты обо мне думаешь, что первое приходит тебе в голову?",
    "Опиши поцелуй, которого ты ждёшь, как будто ты пишешь сцену в книге.",
    "Какую песню ты бы поставила, когда мы снова увидимся?",
]

DREAMS: list[str] = [
    "Опиши нашу кухню через десять лет — что в ней готовится прямо сейчас?",
    "Если бы мы могли проснуться завтра в любой точке мира, где бы мы были?",
    "Какая у нас будет самая странная семейная традиция?",
    "Опиши наш самый обычный вечер — что мы делаем, о чём говорим?",
    "Какой у тебя самый тайный сон про нас?",
    "Если бы мы открыли вместе маленький бизнес, каким бы он был?",
    "Как будет выглядеть наша первая поездка, где мы живём вместе не неделю, а месяц?",
    "Какую глупую привычку мы выработаем вместе?",
    "Если бы у нас был ребёнок, какое первое слово ты бы хотела, чтобы он сказал?",
    "Как мы будем старенькими — что мы всё ещё будем делать вместе?",
]

MISS: list[str] = [
    "Ты сейчас где-то читаешь это, и мне хорошо просто от того, что ты есть. Больше ничего не нужно.",
    "Ты делаешь мою обычную среду лучше, чем любой мой лучший день без тебя. Это странно и это правда.",
    "Иногда я ловлю себя на том, что жду от тебя сообщения, хотя ты мне его уже прислала. Читаю заново, как в первый раз.",
    "Я скучаю так, что хочется позвонить и ничего не говорить, просто слышать, как ты дышишь.",
    "Если бы я мог, я бы сейчас ничего не делал. Просто обнял тебя и молчал бы минут двадцать.",
]

CANT_SLEEP: list[str] = [
    "Закрой глаза. Я рядом — просто подожди меня там, где темно и тихо.",
    "Думай о чём-нибудь хорошем про нас. Я тоже сейчас о тебе думаю.",
    "Засыпать в 3 часа ночи, думая обо мне — это моя слабость. Но всё равно постарайся уснуть, любимая.",
    "Положи телефон. Я знаю, что ты читаешь это уже третий раз. Иди спать, я жду тебя во сне.",
    "Ты не одна. Где бы ты ни была сейчас, я с тобой — в этой тишине, в этой ночи, во всём.",
]

REACTIONS: list[str] = [
    "Это по-настоящему 💌",
    "Запомню, поговорим вечером ❤️",
    "Ого...",
    "Ты серьёзно? 😳",
    "Я читаю это несколько раз",
    "Слишком честно",
    "Ты меня вгоняешь в краску",
    "Об этом я думал последние 20 минут, клянусь",
    "Храню",
    "Ты иногда говоришь такие вещи...",
    "Спасибо, что написала 💛",
    "Жду, когда спросишь меня",
    "Именно поэтому",
    "Никто мне такого не говорил",
    "Перечитаю ещё раз утром",
    "Ты моя любимая",
    "Скучаю прямо сейчас",
    "Улыбаюсь как идиот",
    "Это лучшее, что я прочитал сегодня",
    "Иди сюда 🫂",
]


def _existing_ids(ws: gspread.Worksheet) -> set[str]:
    return {str(r.get("id")) for r in ws.get_all_records() if r.get("id")}


def main() -> int:
    with SECRETS_PATH.open("rb") as f:
        secrets = tomllib.load(f)
    creds = Credentials.from_service_account_info(secrets["gcp_service_account"], scopes=SCOPES)
    sheet = gspread.authorize(creds).open_by_key(secrets["SHEET_ID"])

    questions_ws = sheet.worksheet("questions")
    existing = _existing_ids(questions_ws)
    new_q_rows: list[list[str]] = []
    for i, text in enumerate(FLIRTY, start=1):
        qid = f"flirty_{i:02d}"
        if qid not in existing:
            new_q_rows.append([qid, "flirty", text])
    for i, text in enumerate(DREAMS, start=1):
        qid = f"dreams_{i:02d}"
        if qid not in existing:
            new_q_rows.append([qid, "dreams", text])
    if new_q_rows:
        questions_ws.append_rows(new_q_rows)
    print(f"questions: {len(new_q_rows)} new appended, {len(existing)} already present")

    moods_ws = sheet.worksheet("moods")
    existing_m = _existing_ids(moods_ws)
    new_m_rows: list[list[str]] = []
    for i, text in enumerate(MISS, start=1):
        mid = f"miss_{i}"
        if mid not in existing_m:
            new_m_rows.append([mid, "miss", text])
    for i, text in enumerate(CANT_SLEEP, start=1):
        mid = f"cant_sleep_{i}"
        if mid not in existing_m:
            new_m_rows.append([mid, "cant_sleep", text])
    if new_m_rows:
        moods_ws.append_rows(new_m_rows)
    print(f"moods: {len(new_m_rows)} new appended, {len(existing_m)} already present")

    reactions_ws = sheet.worksheet("reactions")
    existing_r = _existing_ids(reactions_ws)
    new_r_rows: list[list[str]] = []
    for i, text in enumerate(REACTIONS, start=1):
        rid = f"r_{i:02d}"
        if rid not in existing_r:
            new_r_rows.append([rid, text])
    if new_r_rows:
        reactions_ws.append_rows(new_r_rows)
    print(f"reactions: {len(new_r_rows)} new appended, {len(existing_r)} already present")

    return 0


if __name__ == "__main__":
    sys.exit(main())
