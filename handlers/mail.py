from config import ADMIN_IDS
from core.sheets.students_sheet import get_data
from core.sheets.mail_sheet import get_mail_data, reset_texts
from core.keyboards.simple_keyboard import make_simple_keyboard

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardRemove

router = Router()
mail_options = ['Отправить всем', 'Прислать список id', 'Задать параметры', 'Рассылка по таблице']


class SendMail(StatesGroup):
    entering_grades = State()
    choosing_disciplines = State()
    choosing_previous_courses = State()
    choosing_current_courses = State()
    choosing_ids = State()
    entering_mail_text = State()
    deciding_on_photo = State()
    adding_photo = State()
    confirming_mail = State()


def are_grades_correct(grades):
    symbols = '1234567890'
    if grades[0] not in symbols or grades[-1] not in symbols:
        return False
    for symbol in grades:
        if symbol not in f'{symbols}-':
            return False
    if grades.count('-') > 1:
        return False
    if grades.count('-') == 0:
        if int(grades) <= 11:
            return True
        else:
            return False
    else:
        grades = [int(x) for x in grades.split('-')]
        if (grades[0] < grades[1]) and (grades[0] <= 11) and (grades[1] <= 11):
            return True
        else:
            return False


def select_grade(data, grades):
    indexes = []
    if len(grades) == 1:
        for i in range(len(data)):
            if data[i] == grades[0]:
                indexes.append(i)
    else:
        for i in range(len(data)):
            if int(grades[0]) <= int(data[i]) <= int(grades[1]):
                indexes.append(i)
    return indexes


def select_by_criteria(data, items):
    if items == ['+']:
        return [i for i in range(len(data))]
    indexes = []
    for i in range(len(data)):
        flag = 0
        for item in items:
            if item in data[i]:
                flag = 1
                break
        if flag == 1:
            indexes.append(i)
    return indexes


async def send_mail(bot: Bot, criteria, text, filters, photo_id):
    if filters == 'None':
        ids = get_data()[0]
        ids = set(ids[1:])
        for user_id in ids:
            if photo_id is None:
                await bot.send_message(chat_id=user_id, text=text)
            else:
                await bot.send_photo(chat_id=user_id, photo=photo_id, caption=text)

    elif filters == 'ids':
        ids = set(criteria)
        for user_id in ids:
            if photo_id is None:
                await bot.send_message(chat_id=user_id, text=text)
            else:
                await bot.send_photo(chat_id=user_id, photo=photo_id, caption=text)

    elif filters == 'table':
        ids = criteria[0][1:]
        texts = criteria[2][1:]

        for i in range(len(ids)):
            await bot.send_message(chat_id=ids[i], text=texts[i])

        await reset_texts()

    else:
        data = get_data()
        for i in range(len(data)):
            data[i] = data[i][1:]

        ids = data[0]
        grades = select_grade(data[3], criteria[0])
        disciplines = select_by_criteria(data[4], criteria[1])
        previous_courses = select_by_criteria(data[5], criteria[2])
        current_courses = select_by_criteria(data[6], criteria[3])

        recipients_ids = []

        for i in range(len(ids)):
            if (i in grades) and (i in disciplines) and (i in previous_courses) and (i in current_courses):
                recipients_ids.append(ids[i])

        recipients_ids = set(recipients_ids)
        print(recipients_ids)
        for recipient_id in recipients_ids:
            if photo_id is None:
                await bot.send_message(chat_id=recipient_id, text=text)
            else:
                await bot.send_photo(chat_id=recipient_id, photo=photo_id, caption=text)


@router.message(Command(commands=['mail']), lambda message: message.from_user.id in ADMIN_IDS)
async def cmd_mail(message: Message):
    await message.answer(text='Здравствуйте!\n'
                              'Хотите ли Вы отправить рассылку всем или задать параметры выборки? '
                              'Выберите один из вариантов ниже:',
                         reply_markup=make_simple_keyboard(mail_options))


@router.message(F.text.in_(mail_options), lambda message: message.from_user.id in ADMIN_IDS)
async def mail_option_chosen(message: Message, state: FSMContext):
    if message.text == mail_options[0]:
        await message.answer(text='Хорошо, эта рассылка пойдет всем пользователям! '
                                  'Отправьте сообщение с текстом рассылки:',
                             reply_markup=ReplyKeyboardRemove())

        await state.update_data(filters='None')
        await state.set_state(SendMail.entering_mail_text)

    elif message.text == mail_options[1]:
        await message.answer(text='Хорошо! Пришлите список id пользователей\n\n'
                                  'Каждый id пишите с новой строки', reply_markup=ReplyKeyboardRemove())

        await state.update_data(filters='ids')
        await state.set_state(SendMail.choosing_ids)

    elif message.text == mail_options[2]:
        await message.answer(text='Начнем с класса. Введите число или диапазон\n\n'
                                  'Например, 7 или 9-11', reply_markup=ReplyKeyboardRemove())

        await state.update_data(filters='All')
        await state.set_state(SendMail.entering_grades)

    else:
        await message.answer(text='Желаете отправить рассылку по таблице?',
                             reply_markup=make_simple_keyboard(['Подтвердить', 'Отмена']))

        await state.update_data(filters='table', mail_text=None, mail_photo=None)

        await state.set_state(SendMail.confirming_mail)


@router.message(SendMail.entering_grades, F.text,
                lambda message: are_grades_correct(message.text))
async def grades_chosen(message: Message, state: FSMContext):
    grades = message.text
    if len(grades) == 1:
        await state.update_data(grades=[grades])
    else:
        await state.update_data(grades=grades.split('-'))

    await message.answer(text='Отлично!\n'
                              'Теперь введите список предметов, которые интересуют школьников\n\n'
                              'Каждое наименование пишите с новой строки. '
                              'Также можете отправить знак '
                              '+ если подойдут любые предметы')

    await state.set_state(SendMail.choosing_disciplines)


@router.message(SendMail.entering_grades)
async def grades_entered_incorrectly(message: Message):
    await message.answer(text='Некорректное значение классов! Пожалуйста, попробуйте еще раз:')


@router.message(SendMail.choosing_disciplines, F.text)
async def disciplines_chosen(message: Message, state: FSMContext):
    await state.update_data(disciplines=message.text.split('\n'))

    await message.answer(text='Супер!\n'
                              'Теперь введите список кружков, в которых занимались школьники\n\n'
                              'Каждое наименование пишите с новой строки. '
                              'Также можете отправить знак '
                              '+ если значение кружка неважно')

    await state.set_state(SendMail.choosing_previous_courses)


@router.message(SendMail.choosing_previous_courses, F.text)
async def previous_courses_chosen(message: Message, state: FSMContext):
    await state.update_data(previous_courses=message.text.split('\n'))

    await message.answer(text='Остался один фильтр!\n'
                              'Введите список кружков, '
                              'в которых школьники должны заниматься сейчас в том же формате. '
                              'Вы так же можете использовать знак +')

    await state.set_state(SendMail.choosing_current_courses)


@router.message(SendMail.choosing_previous_courses)
async def previous_courses_chosen_incorrectly(message: Message):
    await message.answer('Некорректное значение кружков! '
                         'Пожалуйста, попробуйте еще раз')


@router.message(SendMail.choosing_current_courses, F.text)
async def current_courses_chosen(message: Message, state: FSMContext):
    await state.update_data(current_courses=message.text.split('\n'))

    await message.answer('Все фильтры выбраны! Теперь введите текст рассылки')

    await state.set_state(SendMail.entering_mail_text)


@router.message(SendMail.choosing_current_courses)
async def current_courses_chosen_incorrectly(message: Message):
    await message.answer('Некорректное значение кружков! '
                         'Пожалуйста, попробуйте еще раз')


@router.message(SendMail.choosing_ids, F.text)
async def ids_chosen(message: Message, state: FSMContext):
    await state.update_data(ids=message.text.split('\n'))

    await message.answer(text='Рассылка будет отправлена людям с данными id\n'
                              'Введите, пожалуйста, текст рассылки:', reply_markup=ReplyKeyboardRemove())

    await state.set_state(SendMail.entering_mail_text)


@router.message(SendMail.entering_mail_text, F.text)
async def mail_text_entered(message: Message, state: FSMContext):
    await state.update_data(mail_text=message.text)

    await message.answer(text='Текст принят! Желаете ли добавить фото?',
                         reply_markup=make_simple_keyboard(['Да', 'Нет']))

    await state.set_state(SendMail.deciding_on_photo)


@router.message(SendMail.entering_mail_text)
async def mail_text_entered_incorrectly(message: Message):
    await message.answer(text='Отправьте, пожалуйста, ТЕКСТ рассылки')


@router.message(SendMail.deciding_on_photo, F.text.in_(['Да', 'Нет']))
async def add_photo_or_not(message: Message, state: FSMContext):
    if message.text == 'Да':
        await message.answer(text='Хорошо, отправьте фото, которое хотите прикрепить к рассылке',
                             reply_markup=ReplyKeyboardRemove())

        await state.set_state(SendMail.adding_photo)
    else:
        await state.update_data(mail_photo=None)
        data = await state.get_data()

        await message.answer(text='Ваша рассылка выглядит так:')
        await message.answer(text=data["mail_text"])
        await message.answer('Желаете отправить ее?',
                             reply_markup=make_simple_keyboard(['Подтвердить', 'Отмена']))

        await state.set_state(SendMail.confirming_mail)


@router.message(SendMail.adding_photo, F.photo)
async def photo_added(message: Message, state: FSMContext):
    await state.update_data(mail_photo=message.photo[-1].file_id)

    data = await state.get_data()
    await message.answer(text='Ваша рассылка выглядит так:')
    await message.answer_photo(photo=message.photo[-1].file_id,
                               caption=data["mail_text"])
    await message.answer('Желаете отправить ее?',
                         reply_markup=make_simple_keyboard(['Подтвердить', 'Отмена']))

    await state.set_state(SendMail.confirming_mail)


@router.message(SendMail.adding_photo)
async def photo_added_incorrectly(message: Message):
    await message.answer(text='Не могу распознать фото. Пожалуйста, попробуйте еще раз')


@router.message(SendMail.confirming_mail, F.text.in_(['Подтвердить']))
async def mail_confirmed(message: Message, bot: Bot, state: FSMContext):
    data = await state.get_data()
    if data['filters'] == 'All':
        criteria = [data['grades'], data['disciplines'], data['previous_courses'], data['current_courses']]
    elif data['filters'] == 'ids':
        criteria = data['ids']
    elif data['filters'] == 'table':
        criteria = get_mail_data()
    else:
        criteria = ['-']

    await message.answer('Принято!\nРассылка уже начала расходиться',
                         reply_markup=ReplyKeyboardRemove())

    await send_mail(bot, criteria, data['mail_text'], data['filters'], data['mail_photo'])

    await state.clear()


@router.message(SendMail.confirming_mail, F.text.in_(['Отмена']))
async def cancel_mail(message: Message, state: FSMContext):
    await message.answer(text='Рассылка отменена',
                         reply_markup=ReplyKeyboardRemove())

    await state.clear()
