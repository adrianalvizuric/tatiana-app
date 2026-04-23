"""Telegram bot integration: push Tatiana's answers to Adria, pull his replies back."""
from __future__ import annotations

import requests
import streamlit as st

import data

API_BASE = "https://api.telegram.org/bot{token}"


def _token() -> str:
    return st.secrets["TELEGRAM_BOT_TOKEN"]


def _chat_id() -> str:
    return str(st.secrets["TELEGRAM_CHAT_ID"])


def send_to_adria(*, question_text: str, answer_text: str, asked_adria: bool, local_time: str) -> int | None:
    """DM Adria with Tatiana's answer. Returns the sent message_id (used to match replies)."""
    flag = " ↩️ (хочет твой ответ)" if asked_adria else ""
    body = (
        f"💌 Таня ответила{flag}\n"
        f"🕐 {local_time} (её время)\n\n"
        f"❓ {question_text}\n\n"
        f"💬 {answer_text}"
    )
    resp = requests.post(
        API_BASE.format(token=_token()) + "/sendMessage",
        data={"chat_id": _chat_id(), "text": body},
        timeout=10,
    )
    j = resp.json()
    if not j.get("ok"):
        return None
    return j["result"]["message_id"]


def send_notification(body: str) -> None:
    """Fire-and-forget notification (e.g. 'Таня написала тебе' with no Q/A context)."""
    requests.post(
        API_BASE.format(token=_token()) + "/sendMessage",
        data={"chat_id": _chat_id(), "text": body},
        timeout=10,
    )


def poll_replies() -> int:
    """Fetch new Telegram updates, match Adria's replies to pending answers, write them to Sheets.

    Returns the number of new replies written.
    """
    last_id = int(data.get_state("last_telegram_update_id", "0") or "0")
    offset = last_id + 1 if last_id else None
    params = {"timeout": 0}
    if offset is not None:
        params["offset"] = offset

    resp = requests.get(
        API_BASE.format(token=_token()) + "/getUpdates",
        params=params,
        timeout=10,
    )
    j = resp.json()
    if not j.get("ok"):
        return 0

    updates = j.get("result", [])
    if not updates:
        return 0

    answers_by_msg_id = {a.telegram_message_id: a for a in data.all_answers() if a.telegram_message_id}
    written = 0
    highest_update_id = last_id

    for upd in updates:
        highest_update_id = max(highest_update_id, upd.get("update_id", 0))
        msg = upd.get("message") or upd.get("edited_message")
        if not msg:
            continue
        if str(msg.get("from", {}).get("id")) != _chat_id():
            continue
        reply_to = msg.get("reply_to_message")
        text = msg.get("text", "")
        if not reply_to or not text:
            continue
        replied_msg_id = str(reply_to.get("message_id"))
        answer = answers_by_msg_id.get(replied_msg_id)
        if answer is None or answer.adria_reply:
            continue
        data.write_adria_reply(answer.id, text)
        written += 1

    if highest_update_id > last_id:
        data.set_state("last_telegram_update_id", str(highest_update_id))

    return written
