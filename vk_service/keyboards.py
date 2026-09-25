"""Клавиатуры (кнопки) для сообщений бота."""
import json

from vk_api.keyboard import VkKeyboard, VkKeyboardColor


def _payload(command: str) -> str:
    """Собирает payload кнопки, который бот получит в событии."""
    return json.dumps({"cmd": command})


def candidate_keyboard() -> str:
    """Кнопки под карточкой кандидата."""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button(
        "В избранное",
        color=VkKeyboardColor.POSITIVE,
        payload=_payload("like"),
    )
    keyboard.add_button(
        "Далее",
        color=VkKeyboardColor.PRIMARY,
        payload=_payload("next"),
    )
    keyboard.add_line()
    keyboard.add_button(
        "Избранные",
        color=VkKeyboardColor.SECONDARY,
        payload=_payload("favorites"),
    )
    keyboard.add_button(
        "Новый поиск",
        color=VkKeyboardColor.SECONDARY,
        payload=_payload("search"),
    )
    return keyboard.get_keyboard()


def main_keyboard() -> str:
    """Основные кнопки, когда карточка кандидата не показана."""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button(
        "Новый поиск",
        color=VkKeyboardColor.PRIMARY,
        payload=_payload("search"),
    )
    keyboard.add_button(
        "Избранные",
        color=VkKeyboardColor.SECONDARY,
        payload=_payload("favorites"),
    )
    return keyboard.get_keyboard()


def empty_keyboard() -> str:
    """Пустая клавиатура — убирает кнопки у сообщения."""
    return VkKeyboard.get_empty_keyboard()
