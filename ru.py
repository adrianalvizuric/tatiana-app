"""Russian UI strings. Single source of truth for user-facing text in the app shell.

Deck cards, mood messages, and scripted reactions live in the Google Sheet
(content Adria authors). Strings here are the app chrome Adria does not
edit often.
"""

APP_TITLE = "Письма Тане"

WELCOME_TITLE = "Привет, любимая 💌"
WELCOME_BODY = (
    "Я сделал это для нас — место, где я есть рядом, "
    "даже когда меня нет рядом. Открывай, когда захочешь."
)
WELCOME_BUTTON = "Начать"

NOT_FOUND = "Страница не найдена."

QUESTION_OF_THE_DAY = "Вопрос дня"
NO_QUESTIONS_YET = "Пока нет вопросов — Adria их ещё пишет."
YOUR_ANSWER_PLACEHOLDER = "Напиши свой ответ..."
SEND = "Отправить"
ASK_ADRIA_TOO = "Тоже хочу услышать, что ответит Adria"
ANSWER_SAVED = "Сохранено ✓"
ANSWERED_TODAY = "Ты уже ответила сегодня 💌"
GO_TO_MOODS = "Читать что-нибудь от Adria →"

MOOD_PICKER_TITLE = "Как ты себя чувствуешь?"
MOOD_MISS = "Скучаю"
MOOD_CANT_SLEEP = "Не могу уснуть"

MOOD_EMPTY_STATE = "Больше ничего нового — но я думаю о тебе прямо сейчас."
WRITE_TO_ADRIA = "Написать Adria"
READ_AGAIN = "Прочитать снова"
MESSAGE_SENT_TO_ADRIA = "Я получу это сообщение 💌"

FROM_ADRIA_TAB = "От Adria"
NO_REPLIES_YET = "Пока ничего нового от Adria."

MORE_QUESTIONS = "Ещё вопросы"
BACK = "Назад"

DECK_LABELS = {
    "flirty": "Флирт",
    "dreams": "Мечты",
    "deep":   "Глубокие",
    "silly":  "Глупости",
}

MOOD_LABELS = {
    "miss":       MOOD_MISS,
    "cant_sleep": MOOD_CANT_SLEEP,
}
