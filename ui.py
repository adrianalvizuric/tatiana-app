"""Page renderers. Each function renders one view; state transitions happen via st.rerun()."""
from __future__ import annotations

import random

import streamlit as st

import data
import ru
import telegram


# ---------------------------------------------------------------- helpers

def _today_iso() -> str:
    return data.today_local().isoformat()


def _already_answered_today() -> bool:
    today = _today_iso()
    return any(a.timestamp.startswith(today) for a in data.all_answers())


def _unread_adria_replies() -> int:
    """Replies from Adria that landed since her last visit (very rough: last 24h)."""
    # Simple heuristic for MVP: count all replies that exist. Tab visit clears the badge via session state.
    if st.session_state.get("seen_from_adria_tab"):
        return 0
    return sum(1 for a in data.all_answers() if a.adria_reply)


def _pick_todays_question() -> data.Question | None:
    """Stable daily pick: return today's cached card if set; otherwise pick a random
    unseen card, persist it, and return. None if no questions exist."""
    questions = data.all_questions()
    if not questions:
        return None

    today = data.today_local()
    cached_id = data.daily_pick_for(today)
    if cached_id:
        for q in questions:
            if q.id == cached_id:
                return q

    seen_card_ids = {a.card_id for a in data.all_answers()}
    pool = [q for q in questions if q.id not in seen_card_ids]
    if not pool:
        pool = questions  # pool exhausted → reset

    pick = random.choice(pool)
    data.set_daily_pick(today, pick.id)
    return pick


# ---------------------------------------------------------------- top nav

def render_nav() -> None:
    cols = st.columns([1, 3, 2])
    with cols[0]:
        if st.button("🏠", use_container_width=True, help="Дом"):
            st.session_state["view"] = "home"
            st.rerun()
    with cols[2]:
        count = _unread_adria_replies()
        label = f"💌 {ru.FROM_ADRIA_TAB}" + (f" ({count})" if count else "")
        if st.button(label, use_container_width=True):
            st.session_state["view"] = "from_adria"
            st.rerun()
    st.divider()


# ---------------------------------------------------------------- welcome

def render_welcome() -> None:
    st.title(ru.WELCOME_TITLE)
    st.write(ru.WELCOME_BODY)
    if st.button(ru.WELCOME_BUTTON, type="primary", use_container_width=True):
        data.set_state("first_seen_at", data.now_local().isoformat(timespec="seconds"))
        st.rerun()


# ---------------------------------------------------------------- daily question

def render_daily_question() -> None:
    question = _pick_todays_question()
    if question is None:
        st.info(ru.NO_QUESTIONS_YET)
        return

    today_iso = data.today_local().isoformat()
    todays_answer = next(
        (a for a in data.all_answers()
         if a.card_id == question.id and a.timestamp.startswith(today_iso)),
        None,
    )

    deck_label = ru.DECK_LABELS.get(question.deck, question.deck)
    st.caption(f"{ru.QUESTION_OF_THE_DAY} · {deck_label}")
    st.header(question.text_ru)

    # Already answered today's card → show a done state, not the form
    if todays_answer is not None:
        reaction = st.session_state.pop("last_reaction", None)
        if reaction:
            st.balloons()
            st.success(reaction)
        else:
            st.success(ru.ANSWERED_TODAY)
        with st.container(border=True):
            st.caption("Твой ответ")
            st.write(todays_answer.answer)
        if st.button(ru.GO_TO_MOODS, type="primary", use_container_width=True):
            st.session_state["view"] = "mood_picker"
            st.rerun()
        return

    with st.form("answer_form", clear_on_submit=True):
        answer_text = st.text_area(
            label="answer",
            label_visibility="collapsed",
            placeholder=ru.YOUR_ANSWER_PLACEHOLDER,
            height=140,
        )
        ask_adria = st.checkbox(ru.ASK_ADRIA_TOO, value=False)
        submitted = st.form_submit_button(ru.SEND, type="primary", use_container_width=True)

    if submitted and answer_text.strip():
        answer_id = data.append_answer(question.id, answer_text.strip(), ask_adria)
        msg_id = telegram.send_to_adria(
            question_text=question.text_ru,
            answer_text=answer_text.strip(),
            asked_adria=ask_adria,
            local_time=data.now_local().strftime("%H:%M"),
        )
        if msg_id:
            data.set_answer_telegram_id(answer_id, msg_id)

        reactions = data.all_reactions()
        st.session_state["last_reaction"] = random.choice(reactions) if reactions else ru.ANSWER_SAVED
        st.rerun()


# ---------------------------------------------------------------- mood picker

def render_mood_picker() -> None:
    st.header(ru.MOOD_PICKER_TITLE)
    for mood_key, mood_label in ru.MOOD_LABELS.items():
        if st.button(mood_label, use_container_width=True, key=f"mood_{mood_key}"):
            st.session_state["view"] = "mood_message"
            st.session_state["mood_key"] = mood_key
            st.rerun()


# ---------------------------------------------------------------- mood message

def render_mood_message() -> None:
    mood_key = st.session_state.get("mood_key")
    if not mood_key:
        st.session_state["view"] = "home"
        st.rerun()
        return

    mood_label = ru.MOOD_LABELS.get(mood_key, mood_key)
    st.caption(mood_label)

    pool = [m for m in data.all_moods() if m.mood == mood_key]
    seen = data.mood_seen_ids()
    unseen = [m for m in pool if m.id not in seen]

    # "read_again_id" in session state shows a previously-seen message on demand.
    read_again_id = st.session_state.pop("read_again_id", None)
    if read_again_id:
        chosen = next((m for m in pool if m.id == read_again_id), None)
        if chosen:
            st.write(f"## {chosen.text_ru}")
            _empty_state_actions(mood_key, pool)
            return

    if unseen:
        chosen = random.choice(unseen)
        data.record_mood_seen(chosen.id)
        st.write(f"## {chosen.text_ru}")
        if st.button(ru.BACK, use_container_width=True):
            st.session_state["view"] = "mood_picker"
            st.rerun()
        return

    # Pool exhausted
    st.info(ru.MOOD_EMPTY_STATE)
    _empty_state_actions(mood_key, pool)


def _empty_state_actions(mood_key: str, pool: list[data.MoodMessage]) -> None:
    col1, col2 = st.columns(2)
    with col1:
        if st.button(f"💌 {ru.WRITE_TO_ADRIA}", use_container_width=True):
            telegram.send_notification(f"💭 Таня открыла «{ru.MOOD_LABELS.get(mood_key, mood_key)}» — думает о тебе.")
            st.toast(ru.MESSAGE_SENT_TO_ADRIA)
    with col2:
        if st.button(ru.BACK, use_container_width=True):
            st.session_state["view"] = "mood_picker"
            st.rerun()

    if pool:
        st.caption(ru.READ_AGAIN)
        for m in pool:
            snippet = (m.text_ru[:60] + "...") if len(m.text_ru) > 60 else m.text_ru
            if st.button(snippet, key=f"read_again_{m.id}", use_container_width=True):
                st.session_state["read_again_id"] = m.id
                st.rerun()


# ---------------------------------------------------------------- from adria

def render_from_adria() -> None:
    st.header(f"💌 {ru.FROM_ADRIA_TAB}")
    st.session_state["seen_from_adria_tab"] = True

    replies = [a for a in data.all_answers() if a.adria_reply]
    replies.sort(key=lambda a: a.adria_reply_at, reverse=True)

    if not replies:
        st.info(ru.NO_REPLIES_YET)
        return

    questions_by_id = {q.id: q for q in data.all_questions()}
    for a in replies:
        q = questions_by_id.get(a.card_id)
        if q:
            st.caption(q.text_ru)
        st.write(f"**Ты:** {a.answer}")
        st.write(f"**Adria:** {a.adria_reply}")
        st.caption(a.adria_reply_at)
        st.divider()
