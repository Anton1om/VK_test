"""Слой доступа к данным бота: оборачивает функции database.db_utils."""
from typing import Any, Dict, List, Optional

from database.db_utils import (
    get_candidate,
    get_liked_candidates,
    get_new_candidates,
    get_user,
    mark_candidate_viewed,
    save_candidate,
    save_search_results,
    save_user,
    save_user_search,
)


class BotRepository:

    def get_user(self, vk_id: int):
        """Возвращает пользователя по vk_id или None."""
        return get_user(vk_id)

    def save_user(self, vk_id: int, age: Optional[int] = None,
                  gender: Optional[int] = None,
                  city: Optional[str] = None):
        """Создаёт или обновляет профиль пользователя."""
        return save_user(vk_id, age=age, gender=gender, city=city)

    def save_search(self, vk_id: int, age_from: int, age_to: int,
                    gender: int, city: str):
        """Сохраняет параметры поиска и возвращает его запись."""
        return save_user_search(vk_id, age_from, age_to, gender, city)

    def save_found_candidates(self, search_id: int,
                              found: List[Dict[str, Any]]) -> None:
        """Сохраняет найденных кандидатов и их связь с поиском."""
        candidates = [
            self._vk_user_to_candidate(item)
            for item in found if item.get("id")
        ]
        save_search_results(search_id, candidates)

    def get_candidate(self, vk_id: int):
        """Возвращает кандидата по vk_id или None."""
        return get_candidate(vk_id)

    def get_new_candidates(self, vk_id: int, search_id: int):
        """Возвращает непросмотренных кандидатов поиска."""
        return get_new_candidates(vk_id, search_id)

    def get_liked_candidates(self, vk_id: int):
        """Возвращает избранных кандидатов."""
        return get_liked_candidates(vk_id)

    def mark_viewed(self, vk_id: int, candidate_vk_id: int,
                    is_liked: bool = False) -> None:
        """Отмечает кандидата просмотренным и, при необходимости, избранным."""
        mark_candidate_viewed(vk_id, candidate_vk_id, is_liked=is_liked)

    def save_photos(self, candidate, photos: List[Dict[str, Any]]) -> None:
        """Сохраняет фото кандидата."""
        save_candidate({
            "vk_id": candidate.vk_id,
            "profile_link": candidate.profile_link,
            "name": candidate.name,
            "last_name": candidate.last_name,
            "photos": photos,
        })

    def _vk_user_to_candidate(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Преобразует пользователя из users.search в данные кандидата."""
        vk_id = item["id"]
        return {
            "vk_id": vk_id,
            "profile_link": f"https://vk.com/id{vk_id}",
            "name": item.get("first_name"),
            "last_name": item.get("last_name"),
        }
