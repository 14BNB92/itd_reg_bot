from aiogram.utils.keyboard import ReplyKeyboardMarkup, KeyboardButton


def make_simple_keyboard(items: list[str]) -> ReplyKeyboardMarkup:

    simple_keyboard = []
    for item in items:
        simple_keyboard.append([KeyboardButton(text=item)])
    return ReplyKeyboardMarkup(keyboard=simple_keyboard, resize_keyboard=True)

