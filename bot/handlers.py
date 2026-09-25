"""Логика диалога VKinder: команды, кнопки, профиль, поиск, избранное."""
from typing import Any, Dict, List, Optional

from vk_api.bot_longpoll import VkBotEventType

from bot.bot_utils import (
    calculate_age,
    format_candidate_message,
    format_search_params,
)
from bot.repository import BotRepository
from bot.states import (
    STATE_ASK_AGE,
    STATE_ASK_CITY,
    STATE_ASK_GENDER,
    STATE_IDLE,
    SessionStorage,
)
from config import AGE_DELTA
from vk_service.keyboards import candidate_keyboard, main_keyboard

HELP_TEXT = (
    "Я VKinder — помогаю находить людей для знакомств.\n"
    "Команды и кнопки:\n"
    "• «Новый поиск» — подобрать кандидатов;\n"
    "• «Далее» — показать следующего;\n"
    "• «В избранное» — сохранить текущего;\n"
    "• «Избранные» — показать сохранённых."
)

# Кнопки присылают свой текст, поэтому команду определяем по тексту сообщения
COMMANDS = {
    "начать": "start",
    "старт": "start",
    "/start": "start",
    "поиск": "search",
    "новый поиск": "search",
    "/search": "search",
    "избранные": "favorites",
    "избранное": "favorites",
    "/favorites": "favorites",
    "далее": "next",
    "следующий": "next",
    "в избранное": "like",
    "лайк": "like",
    "помощь": "help",
    "/help": "help",
}


class BotHandlers:
    """Обрабатывает события Long Poll и ведёт диалог с пользователем."""

    def __init__(self, vk, storage: Optional[SessionStorage] = None,
                 repository: Optional[BotRepository] = None) -> None:
        self.vk = vk
        self.storage = storage or SessionStorage()
        self.repo = repository or BotRepository()

    # --- запуск и обработка событий --------------------------------------
    def run(self) -> None:
        """Бесконечный цикл обработки событий Long Poll."""
        for event in self.vk.listen():
            print(f"Событие: {event.type}")
            if event.type == VkBotEventType.MESSAGE_NEW:
                self._safe_handle(event)

    def _safe_handle(self, event) -> None:
        """Ловит ошибки, чтобы бот не падал из-за одного сообщения."""
        try:
            self.handle_message(event)
        except Exception as error:  # noqa: BLE001 — обработчик не должен падать
            print(f"Ошибка при обработке сообщения: {error}")

    def handle_message(self, event) -> None:
        """Точка входа для одного сообщения."""
        message = event.message
        vk_id = message["from_id"]
        peer_id = message["peer_id"]
        text = (message.get("text") or "").strip()
        command = self._resolve_command(text)

        print(f"Сообщение от {vk_id}: {text!r}")

        session = self.storage.get(vk_id)

        # Если идёт уточнение данных профиля — обрабатываем ответ
        if session.state != STATE_IDLE:
            self._process_state_answer(peer_id, vk_id, text, session)
            return

        if command == "start":
            self._handle_start(peer_id, vk_id)
        elif command == "search":
            self._handle_search(peer_id, vk_id, announce=True)
        elif command == "favorites":
            self._show_favorites(peer_id, vk_id)
        elif command == "like":
            self._handle_like(peer_id, vk_id, session)
        elif command == "next":
            self._handle_next(peer_id, vk_id, session)
        else:
            self.vk.send_message(peer_id, HELP_TEXT, keyboard=main_keyboard())

    # --- профиль пользователя --------------------------------------------
    def _handle_start(self, peer_id: int, vk_id: int) -> None:
        self.vk.send_message(
            peer_id,
            "Привет! Я VKinder — помогу найти людей для знакомств.\n"
            "Сначала заполним ваш профиль для поиска.",
        )
        self._after_profile(peer_id, vk_id)

    def _sync_user(self, vk_id: int):
        """Дополняет профиль пользователя данными из VK."""
        info = self.vk.get_user_info(vk_id)
        gender = info.get("sex")
        return self.repo.save_user(
            vk_id,
            age=calculate_age(info.get("bdate")),
            gender=gender if gender in (1, 2) else None,
            city=(info.get("city") or {}).get("title"),
        )

    def _ensure_profile(self, peer_id: int, vk_id: int) -> bool:
        """
        Проверяет, хватает ли данных для поиска.
        Если чего-то нет — задаёт вопрос и возвращает False.
        """
        user = self._sync_user(vk_id)
        session = self.storage.get(vk_id)

        if not user.gender:
            session.state = STATE_ASK_GENDER
            self.vk.send_message(
                peer_id,
                "Укажите ваш пол: «м» (мужской) или «ж» (женский).",
            )
            return False

        if not user.age:
            session.state = STATE_ASK_AGE
            self.vk.send_message(
                peer_id, "Укажите ваш возраст числом (например, 25)."
            )
            return False

        if not user.city:
            session.state = STATE_ASK_CITY
            self.vk.send_message(peer_id, "Укажите ваш город.")
            return False

        session.state = STATE_IDLE
        return True

    def _process_state_answer(self, peer_id: int, vk_id: int,
                              text: str, session) -> None:
        """Обрабатывает ответ пользователя на уточняющий вопрос."""
        if session.state == STATE_ASK_GENDER:
            gender = self._parse_gender(text)
            if gender is None:
                self.vk.send_message(
                    peer_id, "Не понял пол. Напишите «м» или «ж»."
                )
                return
            self.repo.save_user(vk_id, gender=gender)

        elif session.state == STATE_ASK_AGE:
            age = self._parse_age(text)
            if age is None:
                self.vk.send_message(
                    peer_id, "Возраст должен быть числом от 14 до 100."
                )
                return
            self.repo.save_user(vk_id, age=age)

        elif session.state == STATE_ASK_CITY:
            self.repo.save_user(vk_id, city=text)

        session.state = STATE_IDLE
        self._after_profile(peer_id, vk_id)

    def _after_profile(self, peer_id: int, vk_id: int) -> None:
        """Когда профиль заполнен — сразу предлагаем поиск."""
        if self._ensure_profile(peer_id, vk_id):
            self._handle_search(peer_id, vk_id, announce=True)

    # --- поиск ------------------------------------------------------------
    def _handle_search(self, peer_id: int, vk_id: int,
                       announce: bool = False) -> None:
        """Запускает новый поиск и показывает первого кандидата."""
        user = self.repo.get_user(vk_id)
        if not user or not user.gender or not user.age or not user.city:
            self._ensure_profile(peer_id, vk_id)
            return

        sex = 3 - user.gender  # ищем противоположный пол
        age_from = max(18, user.age - AGE_DELTA)
        age_to = user.age + AGE_DELTA

        if announce:
            self.vk.send_message(
                peer_id, format_search_params(user, age_from, age_to, sex)
            )

        session = self.storage.get(vk_id)
        session.state = STATE_IDLE
        session.queue = []
        session.current = None

        try:
            city_id = self.vk.get_city_id(user.city)
            found = self.vk.search_users(
                sex=sex, age_from=age_from, age_to=age_to, city_id=city_id
            )
        except Exception as error:  # noqa: BLE001
            print(f"Ошибка поиска для пользователя {vk_id}: {error}")
            self.vk.send_message(
                peer_id,
                "Не удалось выполнить поиск. Попробуйте позже.",
                keyboard=main_keyboard(),
            )
            return

        search = self.repo.save_search(vk_id, age_from, age_to, sex, user.city)
        self.repo.save_found_candidates(search.id, found)
        session.search_id = search.id

        self.vk.send_message(peer_id, "Начинаю показывать кандидатов 👇")
        self._show_next_candidate(peer_id, vk_id, session)

    # --- показ кандидатов -------------------------------------------------
    def _handle_next(self, peer_id: int, vk_id: int, session) -> None:
        if session.current is None and not session.queue:
            self.vk.send_message(
                peer_id, "Сначала запустите поиск.", keyboard=main_keyboard()
            )
            return
        self._show_next_candidate(peer_id, vk_id, session)

    def _handle_like(self, peer_id: int, vk_id: int, session) -> None:
        if session.current is None:
            self.vk.send_message(
                peer_id,
                "Сейчас нет активного кандидата.",
                keyboard=main_keyboard(),
            )
            return

        self.repo.mark_viewed(vk_id, session.current["vk_id"], is_liked=True)
        self.vk.send_message(peer_id, "Добавил в избранное ❤")
        self._show_next_candidate(peer_id, vk_id, session)

    def _show_next_candidate(self, peer_id: int, vk_id: int, session) -> None:
        """Показывает следующего кандидата или сообщает, что их нет."""
        candidate = self._pop_candidate(vk_id, session)
        if candidate is None:
            session.current = None
            self.vk.send_message(
                peer_id,
                "Кандидаты закончились. "
                "Нажмите «Новый поиск», чтобы найти ещё.",
                keyboard=main_keyboard(),
            )
            return

        photos = self._ensure_photos(candidate)
        self.repo.mark_viewed(vk_id, candidate.vk_id, is_liked=False)
        session.current = {"vk_id": candidate.vk_id}

        attachment = ",".join(
            photo["attachment"] for photo in photos
        ) or None
        self.vk.send_message(
            peer_id,
            format_candidate_message({
                "vk_id": candidate.vk_id,
                "name": candidate.name,
                "last_name": candidate.last_name,
                "profile_link": candidate.profile_link,
            }),
            attachment=attachment,
            keyboard=candidate_keyboard(),
        )

    def _pop_candidate(self, vk_id: int, session):
        """Достаёт следующего кандидата из очереди, пополняя её из БД."""
        if not session.queue and session.search_id is not None:
            remaining = self.repo.get_new_candidates(vk_id, session.search_id)
            session.queue = [item.vk_id for item in remaining]

        while session.queue:
            candidate = self.repo.get_candidate(session.queue.pop(0))
            if candidate is not None:
                return candidate
        return None

    def _ensure_photos(self, candidate) -> List[Dict[str, Any]]:
        """Возвращает фото кандидата, подгружая их при необходимости."""
        if candidate.photos:
            return candidate.photos

        photos = self.vk.get_top_photos(candidate.vk_id)
        self.repo.save_photos(candidate, photos)
        return photos

    # --- избранное --------------------------------------------------------
    def _show_favorites(self, peer_id: int, vk_id: int) -> None:
        liked = self.repo.get_liked_candidates(vk_id)
        if not liked:
            self.vk.send_message(
                peer_id, "В избранном пока пусто.", keyboard=main_keyboard()
            )
            return

        self.vk.send_message(
            peer_id,
            f"Избранные кандидаты: {len(liked)}",
            keyboard=main_keyboard(),
        )
        for candidate in liked:
            photos = candidate.photos or []
            attachment = ",".join(
                photo["attachment"]
                for photo in photos if photo.get("attachment")
            ) or None
            self.vk.send_message(
                peer_id,
                format_candidate_message({
                    "vk_id": candidate.vk_id,
                    "name": candidate.name,
                    "last_name": candidate.last_name,
                    "profile_link": candidate.profile_link,
                }),
                attachment=attachment,
            )

    # --- разбор ввода -----------------------------------------------------
    def _resolve_command(self, text: str) -> Optional[str]:
        """Определяет команду по тексту сообщения (кнопки присылают текст)."""
        return COMMANDS.get(text.strip().lower())

    def _parse_gender(self, text: str) -> Optional[int]:
        """Преобразует ответ пользователя в код пола VK: 1 — ж, 2 — м."""
        value = text.strip().lower()
        if value in ("м", "муж", "мужской", "m", "male", "2"):
            return 2
        if value in ("ж", "жен", "женский", "f", "female", "1"):
            return 1
        return None

    def _parse_age(self, text: str) -> Optional[int]:
        """Проверяет, что введён корректный возраст."""
        if text.isdigit() and 14 <= int(text) <= 100:
            return int(text)
        return None
