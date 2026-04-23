"""Google Sheets data access. Every read/write to the Tatiana Sheet goes through here."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import gspread
import pytz
import streamlit as st
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


# ---------------------------------------------------------------- connection

@st.cache_resource
def _sheet() -> gspread.Spreadsheet:
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]), scopes=SCOPES
    )
    return gspread.authorize(creds).open_by_key(st.secrets["SHEET_ID"])


def _ws(name: str) -> gspread.Worksheet:
    return _sheet().worksheet(name)


def user_tz() -> pytz.BaseTzInfo:
    return pytz.timezone(st.secrets.get("USER_TZ", "Europe/Madrid"))


def now_local() -> datetime:
    return datetime.now(user_tz())


def today_local() -> date:
    return now_local().date()


# ---------------------------------------------------------------- models

@dataclass(frozen=True)
class Question:
    id: str
    deck: str
    text_ru: str


@dataclass(frozen=True)
class MoodMessage:
    id: str
    mood: str
    text_ru: str


@dataclass(frozen=True)
class Answer:
    id: str
    timestamp: str
    card_id: str
    answer: str
    asked_adria: bool
    telegram_message_id: str
    adria_reply: str
    adria_reply_at: str


# ---------------------------------------------------------------- reads

@st.cache_data(ttl=60)
def all_questions() -> list[Question]:
    rows = _ws("questions").get_all_records()
    return [Question(str(r["id"]), r["deck"], r["text_ru"]) for r in rows if r.get("id")]


@st.cache_data(ttl=60)
def all_moods() -> list[MoodMessage]:
    rows = _ws("moods").get_all_records()
    return [MoodMessage(str(r["id"]), r["mood"], r["text_ru"]) for r in rows if r.get("id")]


@st.cache_data(ttl=60)
def all_reactions() -> list[str]:
    rows = _ws("reactions").get_all_records()
    return [r["text_ru"] for r in rows if r.get("text_ru")]


@st.cache_data(ttl=30)
def all_answers() -> list[Answer]:
    rows = _ws("answers").get_all_records()
    answers = []
    for r in rows:
        if not r.get("id"):
            continue
        answers.append(Answer(
            id=str(r["id"]),
            timestamp=str(r.get("timestamp", "")),
            card_id=str(r.get("card_id", "")),
            answer=str(r.get("answer", "")),
            asked_adria=str(r.get("asked_adria", "")).lower() in ("true", "1", "yes"),
            telegram_message_id=str(r.get("telegram_message_id", "")),
            adria_reply=str(r.get("adria_reply", "")),
            adria_reply_at=str(r.get("adria_reply_at", "")),
        ))
    return answers


@st.cache_data(ttl=30)
def mood_seen_ids() -> set[str]:
    rows = _ws("mood_seen").get_all_records()
    return {str(r["mood_id"]) for r in rows if r.get("mood_id")}


@st.cache_data(ttl=30)
def daily_pick_for(d: date) -> str | None:
    rows = _ws("daily_pick").get_all_records()
    for r in rows:
        if str(r.get("date")) == d.isoformat():
            return str(r["card_id"])
    return None


def _invalidate_all_caches() -> None:
    all_questions.clear()
    all_moods.clear()
    all_reactions.clear()
    all_answers.clear()
    mood_seen_ids.clear()
    daily_pick_for.clear()


# ---------------------------------------------------------------- writes

def set_daily_pick(d: date, card_id: str) -> None:
    _ws("daily_pick").append_row([d.isoformat(), card_id])
    daily_pick_for.clear()


def append_answer(card_id: str, answer_text: str, asked_adria: bool) -> str:
    answer_id = uuid.uuid4().hex[:10]
    _ws("answers").append_row([
        answer_id,
        now_local().isoformat(timespec="seconds"),
        card_id,
        answer_text,
        "true" if asked_adria else "false",
        "",  # telegram_message_id — filled by telegram.send_to_adria
        "",  # adria_reply
        "",  # adria_reply_at
    ])
    all_answers.clear()
    return answer_id


def set_answer_telegram_id(answer_id: str, message_id: str | int) -> None:
    ws = _ws("answers")
    cell = ws.find(answer_id, in_column=1)
    if cell is not None:
        ws.update_cell(cell.row, 6, str(message_id))
    all_answers.clear()


def write_adria_reply(answer_id: str, reply_text: str) -> None:
    ws = _ws("answers")
    cell = ws.find(answer_id, in_column=1)
    if cell is not None:
        ws.update_cell(cell.row, 7, reply_text)
        ws.update_cell(cell.row, 8, now_local().isoformat(timespec="seconds"))
    all_answers.clear()


def record_mood_seen(mood_id: str) -> None:
    _ws("mood_seen").append_row([mood_id, now_local().isoformat(timespec="seconds")])
    mood_seen_ids.clear()


# ---------------------------------------------------------------- state tab

@st.cache_data(ttl=30)
def _state_rows() -> dict[str, str]:
    rows = _ws("state").get_all_records()
    return {str(r["key"]): str(r.get("value", "")) for r in rows if r.get("key")}


def get_state(key: str, default: str = "") -> str:
    return _state_rows().get(key, default)


def set_state(key: str, value: Any) -> None:
    ws = _ws("state")
    cell = ws.find(key, in_column=1)
    if cell is None:
        ws.append_row([key, str(value)])
    else:
        ws.update_cell(cell.row, 2, str(value))
    _state_rows.clear()
