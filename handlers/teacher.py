from core.sheets.students_sheet import get_data
from core.sheets.teachers_sheet import get_teacher_data
from core.sheets.teachers_payment_sheet import check_payment_amount
from core.keyboards.simple_keyboard import make_simple_keyboard
from core.keyboards.simple_inline import make_simple_inline
from core.keyboards.yes_no_inline import make_yes_no_inline
from core.sheets.teacher_schedule_sheet import get_schedule, update_sheet

from aiogram import Bot, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

router = Router()

teacher_options = ['Проверить зарплату', 'Отправить обратную связь по ребенку']


class Teacher(StatesGroup):
    choosing_action = State()
    choosing_group = State()
    choosing_child = State()
    entering_text = State()
    confirming_text = State()


def check_teacher(teacher_id):
    data = get_teacher_data()

    if str(teacher_id) in data[0]:
        return True

    return False


def check_group(teacher_id, group):
    data = get_teacher_data()
    ind = data[0].index(str(teacher_id))

    if group in data[2][ind]:
        return True

    return False


def select_children(group):
    data = get_data()
    ids = data[0]
    names = data[1]
    courses = data[6]

    keyboard = []

    for i in range(len(ids)):
        if group in courses[i]:
            keyboard.append([names[i], f'{names[i]}/////{ids[i]}'])

    return keyboard


@router.message(Command(commands=['teacher']), lambda message: check_teacher(message.from_user.id))
async def cmd_teacher(message: Message, state: FSMContext):
    data = get_teacher_data()
    teacher_id = message.from_user.id
    ind = data[0].index(str(teacher_id))
    teacher_name = data[1][ind]

    await message.answer(text=f'Здравствуйте, {teacher_name}!'
                              'Используйте кнопки снизу для реализации функционала, доступного Вам:',
                         reply_markup=make_simple_keyboard(teacher_options))

    await state.set_state(Teacher.choosing_action)
    await state.update_data(teacher_name=teacher_name)


@router.message(Teacher.choosing_action, F.text.in_(teacher_options))
async def action_chosen(message: Message, state: FSMContext):
    if message.text == teacher_options[0]:
        data = await state.get_data()
        payment_amount = check_payment_amount(data['teacher_name'])

        await message.answer(text=f'Мы должны заплатить Вам {payment_amount} рублей',
                             reply_markup=ReplyKeyboardRemove())

    else:
        await message.answer(text='Введите название группы, по ребенку которой Вы '
                                  'хотите отправить обратную связь',
                             reply_markup=ReplyKeyboardRemove())

        await state.set_state(Teacher.choosing_group)


@router.message(Teacher.choosing_action)
async def action_chosen_incorrectly(message: Message):
    await message.answer(text='Некорректное действие! Пожалуйста, выберите один из вариантов ниже:')


@router.message(Teacher.choosing_group, F.text)
async def group_chosen(message: Message, state: FSMContext):
    teacher_id = message.from_user.id
    group = message.text

    if check_group(teacher_id, group):
        await message.answer(text='Принято!\n'
                                  'Теперь выберите ребенка, по которому хотите отправить обратную связь:',
                             reply_markup=make_simple_inline(select_children(group)))

        await state.update_data(group=group)
        await state.set_state(Teacher.choosing_child)

    else:
        await message.answer(text='Извините, похоже, Вы не ведете в данной группе. '
                                  'Пожалуйста, попробуйте еще раз:')


@router.message(Teacher.entering_text, F.text)
async def text_entered(message: Message, state: FSMContext):
    data = await state.get_data()
    text = f'Обратная связь\n' \
           f'Ученик: {data["child_name"]}\n'\
           f'Группа: {data["group"]}\n'\
           f'Преподаватель: {data["teacher_name"]}\n\n' + message.text

    await message.answer(text='Сейчас Ваше сообщение выглядит так:')
    await message.answer(text=text)
    await message.answer(text='Желаете отправить его?',
                         reply_markup=make_yes_no_inline())

    await state.update_data(text=text)
    await state.set_state(Teacher.confirming_text)


@router.message(Teacher.entering_text)
async def text_entered_incorrectly(message: Message):
    await message.answer(text='Что-то пошло не так! Попробуйте ввести текст рассылки снова:')


@router.callback_query(Teacher.choosing_child)
async def child_chosen(call: CallbackQuery, state: FSMContext):
    data = call.data.split('/////')
    await state.update_data(child_name=data[0], child_id=data[1])

    await call.message.edit_text(text='Хорошо! Теперь введите текст сообщения:')

    await state.set_state(Teacher.entering_text)

    await call.answer()


@router.callback_query(Teacher.confirming_text, lambda call: call.data in ['yes', 'no'])
async def text_confirmed(call: CallbackQuery, state: FSMContext, bot: Bot):
    answer = call.data

    if answer == 'yes':
        data = await state.get_data()

        await call.message.edit_text(text='Сообщение отправлено!')
        await bot.send_message(chat_id=data['child_id'], text=data['text'])

        await state.clear()
    else:
        await call.message.edit_text(text='Введите текст сообщения заново:')

        await state.set_state(Teacher.entering_text)

    await call.answer()


@router.callback_query(lambda call: '@@yes' in call.data or '@@no' in call.data)
async def lesson_confirmation(call: CallbackQuery):
    data = call.data.split('@@')
    teacher_id = data[0]
    lesson_day = int(data[1])
    group_name = f'{data[3]} {data[2]}'

    if data[4] == 'yes':
        answer = 'да'
    else:
        answer = 'нет'

    data = get_schedule()
    ids = data['ids+names'][0]
    ind = ids.index(teacher_id)

    if lesson_day < 3:
        schedule = data['mon-wen']
    else:
        schedule = data['thu-sun']

    groups = schedule[lesson_day][ind].split('\n')
    finite_groups = ''

    for group in groups:
        if finite_groups == '':
            s = ''
        else:
            s = '\n'
        if group == group_name:
            finite_groups += s + f'{group_name} ({answer})'
        else:
            finite_groups += s + f'{group}'

    await update_sheet(ind + 2, lesson_day, finite_groups)

    await call.message.edit_text(text='Спасибо за Ваш ответ!')

    await call.answer()