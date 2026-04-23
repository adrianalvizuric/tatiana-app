"""Entry point: auth gate, welcome once, adaptive landing, top nav, view dispatch."""
from __future__ import annotations

import streamlit as st

import data
import ru
import telegram
import ui


def _authorized() -> bool:
    if st.secrets.get("DEV_MODE", False):
        return True
    key = st.query_params.get("key", "")
    return key == st.secrets.get("APP_KEY", "")


def _first_time() -> bool:
    return not data.get_state("first_seen_at")


def _resolve_home_view() -> str:
    already = any(a.timestamp.startswith(data.today_local().isoformat()) for a in data.all_answers())
    return "mood_picker" if already else "daily_question"


def main() -> None:
    st.set_page_config(page_title=ru.APP_TITLE, page_icon="💌", layout="centered")

    if not _authorized():
        st.write(ru.NOT_FOUND)
        return

    if _first_time():
        ui.render_welcome()
        return

    try:
        telegram.poll_replies()
    except Exception:
        pass  # network hiccups shouldn't break the page

    view = st.session_state.get("view", "home")
    if view == "home":
        view = _resolve_home_view()
        st.session_state["view"] = view

    ui.render_nav()

    if view == "daily_question":
        ui.render_daily_question()
    elif view == "mood_picker":
        ui.render_mood_picker()
    elif view == "mood_message":
        ui.render_mood_message()
    elif view == "from_adria":
        ui.render_from_adria()
    else:
        st.session_state["view"] = "home"
        st.rerun()


if __name__ == "__main__":
    main()
