"""Состояния диалога с пользователем и их хранение в памяти."""
from typing import Dict, List, Optional

# Состояния уточнения данных профиля
STATE_IDLE = "idle"
STATE_ASK_GENDER = "ask_gender"
STATE_ASK_AGE = "ask_age"
STATE_ASK_CITY = "ask_city"


class UserSession:
    """Текущее состояние диалога с одним пользователем."""

    def __init__(self):
        self.state: str = STATE_IDLE
        self.search_id: Optional[int] = None       # id последнего поиска
        self.queue: List[int] = []                 # vk_id кандидатов к показу
        self.current: Optional[dict] = None        # кандидат, показанный сейчас


class SessionStorage:
    """
    Простое хранилище состояний в памяти. Живёт, пока работает бот.
    Все значимые данные (профиль, поиски, реакции) при этом сохраняются в БД.
    """

    def __init__(self):
        self._sessions: Dict[int, UserSession] = {}

    def get(self, vk_id: int) -> UserSession:
        """Возвращает сессию пользователя, создавая её при первом обращении."""
        if vk_id not in self._sessions:
            self._sessions[vk_id] = UserSession()
        return self._sessions[vk_id]

    def reset(self, vk_id: int) -> UserSession:
        """Сбрасывает сессию пользователя."""
        self._sessions[vk_id] = UserSession()
        return self._sessions[vk_id]
