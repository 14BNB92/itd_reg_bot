from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton


def make_yes_no_inline(custom_callbacks=None):
    if custom_callbacks is None:
        btn1 = InlineKeyboardButton(text='Да', callback_data='yes')
        btn2 = InlineKeyboardButton(text='Нет', callback_data='no')
    else:
        btn1 = InlineKeyboardButton(text='Да', callback_data=custom_callbacks[0])
        btn2 = InlineKeyboardButton(text='Нет', callback_data=custom_callbacks[1])
    builder = InlineKeyboardBuilder()
    builder.row(btn1, btn2)

    return builder.as_markup()
