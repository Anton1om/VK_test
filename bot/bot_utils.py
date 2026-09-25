"""Вспомогательные функции бота: возраст и тексты сообщений."""
from datetime import date
from typing import Any, Dict, Optional

GENDER_TITLES = {1: "женский", 2: "мужской"}


def calculate_age(bdate: Optional[str]) -> Optional[int]:
    """
    Считает возраст по строке даты рождения ВКонтакте.
    Формат bdate: «Д.М.ГГГГ» или «Д.М».
    Если год не указан (или данные некорректны) — возвращает None.
    """
    if not bdate:
        return None

    parts = bdate.split(".")
    if len(parts) != 3:
        return None

    try:
        day, month, year = (int(part) for part in parts)
    except ValueError:
        return None

    today = date.today()
    age = today.year - year
    if (today.month, today.day) < (month, day):
        age -= 1

    if age < 0 or age > 120:
        return None
    return age


def format_candidate_message(candidate: Dict[str, Any]) -> str:
    """Формирует текст сообщения с информацией о кандидате."""
    full_name = " ".join(
        part for part in (candidate.get("name"), candidate.get("last_name"))
        if part
    )
    link = candidate.get("profile_link")
    if not link:
        link = f"https://vk.com/id{candidate.get('vk_id')}"
    return f"{full_name}\n{link}"


def format_search_params(user, age_from: int, age_to: int, sex: int) -> str:
    """Формирует текст с параметрами предстоящего поиска."""
    gender = GENDER_TITLES.get(sex, "любой")
    city = user.city or "любой"
    return (
        "Параметры поиска:\n"
        f"• пол: {gender}\n"
        f"• город: {city}\n"
        f"• возраст: от {age_from} до {age_to}"
    )
