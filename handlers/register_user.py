import datetime
from core.sheets.students_sheet import register_user, get_data

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardRemove


class RegisterUser(StatesGroup):
    entering_name = State()
    entering_birthday = State()
    entering_grade = State()
    choosing_disciplines = State()
    entering_previous_groups = State()


def not_registered(user_id):
    user_ids = get_data()[0]
    if str(user_id) in user_ids:
        return False
    else:
        return True


def is_date_correct(date_text):
    try:
        date_text = date_text.split('.')
        date_text = '-'.join(date_text[::-1])
        datetime.date.fromisoformat(date_text)
        return True
    except ValueError:
        return False


def is_grade_correct(item):
    for symbol in item:
        if symbol not in '1234567890':
            return False
    if int(item) > 11:
        return False
    return True


router = Router()


@router.message(Command(commands=['register']))
async def cmd_register(message: Message, state: FSMContext):
    await message.answer(text='Введите, пожалуйста, ФИО ребенка (отчество при наличии)',
                         reply_markup=ReplyKeyboardRemove())

    await state.set_state(RegisterUser.entering_name)


@router.message(RegisterUser.entering_name, F.text, lambda message: 2 <= len(message.text.split()) <= 3)
async def name_entered(message: Message, state: FSMContext):
    await state.update_data(name=message.text)

    await message.answer(text=f'Теперь введите дату рождения ребенка формате ДД.ММ.ГГГГ\n\n')

    await state.set_state(RegisterUser.entering_birthday)


@router.message(RegisterUser.entering_name)
async def name_entered_incorrectly(message: Message):
    await message.answer(text='Некорректное значение имени!\n\n'
                              'Пожалуйста, попробуйте еще раз:')


@router.message(RegisterUser.entering_birthday, F.text,
                lambda message: is_date_correct(message.text))
async def birthday_entered(message: Message, state: FSMContext):
    await state.update_data(birthday=message.text)

    await message.answer(text='Отлично! Теперь скажите,'
                              'в каком классе учится ребенок?\n\n'
                              'В сообщении напишите просто число. Например, 7')

    await state.set_state(RegisterUser.entering_grade)


@router.message(RegisterUser.entering_birthday)
async def birthday_entered_incorrectly(message: Message):
    await message.answer('Некорректное значение! Дата должна быть введена в формате ДД.ММ.ГГГГ\n\n'
                         'Например, 23 августа 2005 г. будет выглядеть как 23.08.2005')


@router.message(RegisterUser.entering_grade, F.text,
                lambda message: is_grade_correct(message.text))
async def grade_entered(message: Message, state: FSMContext):
    await state.update_data(grade=message.text)

    await message.answer(text='Супер, осталось совсем немного!\n'
                              'Какие предметы интересуют ребенка? Присылайте название каждого '
                              'предмета с новой строки\n\n'
                              'Например:\nФизика\nМатематика\nПрограммирование\n')

    await state.set_state(RegisterUser.choosing_disciplines)


@router.message(RegisterUser.choosing_disciplines, F.text)
async def previous_groups_entered(message: Message, state: FSMContext):
    await state.update_data(disciplines=message.text)

    user_data = await state.get_data()
    user_id = message.from_user.id
    name = user_data['name']
    birthday = user_data['birthday']
    grade = user_data['grade']
    disciplines = user_data['disciplines']

    await register_user(user_id, name, birthday, grade, disciplines)

    await message.answer('Поздравлем, ребенок зарегистрирован!')

    await state.clear()