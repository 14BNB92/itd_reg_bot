from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardBuilder


def make_simple_inline(items: list[list[str]]):
    builder = InlineKeyboardBuilder()

    for item in items:
        if len(item) == 2:
            builder.row(InlineKeyboardButton(text=item[0], callback_data=item[1]))
        else:
            builder.row(InlineKeyboardButton(text=item[0], callback_data=item[1], url=item[2], extra_data=item[3]))

    return builder.as_markup()