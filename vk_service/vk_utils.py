"""Вспомогательные функции для работы с фото ВКонтакте."""
from typing import Any, Dict, List, Optional

from config import PHOTO_COUNT


def photo_to_attachment(photo: Dict[str, Any]) -> Optional[str]:
    """
    Превращает объект фото VK в attachment вида
    «photo{owner_id}_{id}» (или «photo{owner_id}_{id}_{access_key}»).
    """
    owner_id = photo.get("owner_id")
    photo_id = photo.get("id")
    if owner_id is None or photo_id is None:
        return None

    attachment = f"photo{owner_id}_{photo_id}"
    access_key = photo.get("access_key")
    if access_key:
        attachment += f"_{access_key}"
    return attachment


def pick_top_photos(photos: List[Dict[str, Any]],
                    limit: int = PHOTO_COUNT) -> List[Dict[str, Any]]:
    """
    Оставляет самые популярные фотографии.
    Популярность определяется количеством лайков (photo['likes']['count']).
    """
    def likes_count(photo: Dict[str, Any]) -> int:
        likes = photo.get("likes") or {}
        return likes.get("count") or 0

    return sorted(photos, key=likes_count, reverse=True)[:limit]
