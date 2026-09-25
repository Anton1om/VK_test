"""Обёртка над API ВКонтакте: профиль, поиск, фото, сообщения."""
from typing import Any, Dict, List, Optional

import vk_api
from vk_api.bot_longpoll import VkBotLongPoll
from vk_api.utils import get_random_id

from config import PHOTO_COUNT, SEARCH_COUNT, VK_API_VERSION, VK_GROUP_TOKEN, VK_USER_TOKEN

from vk_service.vk_utils import photo_to_attachment, pick_top_photos


class VkClient:
    """
    Клиент ВКонтакте.

    Использует две сессии:
      * групповую — токен сообщества (Long Poll, отправка сообщений);
      * пользовательскую — токен пользователя
        (users.get, users.search, photos.get).
    """

    def __init__(self) -> None:
        if not VK_GROUP_TOKEN:
            raise ValueError("Не задан VK_GROUP_TOKEN (см. .env)")
        if not VK_USER_TOKEN:
            raise ValueError("Не задан VK_USER_TOKEN (см. .env)")

        self.group_session = vk_api.VkApi(
            token=VK_GROUP_TOKEN, api_version=VK_API_VERSION
        )
        self.group_api = self.group_session.get_api()

        # ID сообщества определяем по ключу доступа сообщества
        self.group_id = self._resolve_group_id()
        self.longpoll = VkBotLongPoll(self.group_session, self.group_id)

        self.user_session = vk_api.VkApi(
            token=VK_USER_TOKEN, api_version=VK_API_VERSION
        )
        self.user_api = self.user_session.get_api()

    def _resolve_group_id(self) -> int:
        """
        Возвращает id сообщества, которому принадлежит VK_GROUP_TOKEN.

        groups.getById без параметров, вызванный с ключом доступа сообщества,
        возвращает само это сообщество.
        """
        response = self.group_api.groups.getById()
        if isinstance(response, dict):
            groups = response.get("groups") or response.get("items") or []
        else:
            groups = response or []
        if not groups:
            raise ValueError(
                "Не удалось определить ID сообщества по VK_GROUP_TOKEN"
            )
        return groups[0]["id"]

    def listen(self):
        """Возвращает генератор событий Long Poll."""
        return self.longpoll.listen()

    def get_user_info(self, vk_id: int) -> Dict[str, Any]:
        """
        Возвращает данные пользователя из VK (пол, город, дата рождения)
        или пустой словарь, если получить их не удалось.
        """
        response = self.user_api.users.get(
            user_ids=vk_id, fields="bdate,city,sex"
        )
        if not response:
            return {}
        return response[0]

    def get_city_id(self, city_name: Optional[str]) -> Optional[int]:
        """Ищет идентификатор города по названию (database.getCities)."""
        if not city_name:
            return None
        try:
            response = self.user_api.database.getCities(
                country_id=1, q=city_name, count=1
            )
        except vk_api.exceptions.ApiError:
            return None

        items = (response or {}).get("items") or []
        if not items:
            return None
        return items[0].get("id")

    def search_users(self, sex: int, age_from: int, age_to: int,
                     city_id: Optional[int] = None,
                     count: int = SEARCH_COUNT) -> List[Dict[str, Any]]:
        """
        Ищет пользователей ВКонтакте по заданным параметрам.
        пол: 1 — женский, 2 — мужской (для поиска передаём противоположный).
        """
        params: Dict[str, Any] = {
            "sex": sex,
            "age_from": age_from,
            "age_to": age_to,
            "has_photo": 1,
            "count": count,
            "sort": 0,
            "fields": "city,sex,bdate",
        }
        if city_id:
            params["city"] = city_id

        response = self.user_api.users.search(**params)
        if not response:
            return []
        return response.get("items", [])

    def get_top_photos(self, vk_id: int,
                       limit: int = PHOTO_COUNT) -> List[Dict[str, Any]]:
        """
        Возвращает до `limit` самых популярных фото профиля.

        Каждый элемент — словарь с ключами:
          * attachment — строка для messages.send (photo...);
          * likes — количество лайков (для сортировки).
        """
        try:
            response = self.user_api.photos.get(
                owner_id=vk_id,
                album_id="profile",
                extended=1,
                count=50,
                photo_sizes=0,
            )
        except vk_api.exceptions.ApiError:
            # Профиль может быть закрыт или фото недоступны
            return []

        items = (response or {}).get("items") or []
        top_photos = pick_top_photos(items, limit=limit)

        result: List[Dict[str, Any]] = []
        for photo in top_photos:
            attachment = photo_to_attachment(photo)
            if not attachment:
                continue
            likes = (photo.get("likes") or {}).get("count") or 0
            result.append({"attachment": attachment, "likes": likes})
        return result

    def send_message(self, peer_id: int, message: str,
                     keyboard: Optional[str] = None,
                     attachment: Optional[str] = None) -> None:
        """Отправляет сообщение пользователю от имени сообщества."""
        params: Dict[str, Any] = {
            "peer_id": peer_id,
            "message": message,
            "random_id": get_random_id(),
        }
        if keyboard is not None:
            params["keyboard"] = keyboard
        if attachment:
            params["attachment"] = attachment

        self.group_api.messages.send(**params)
