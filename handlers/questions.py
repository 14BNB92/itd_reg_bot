import sqlite3

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from aiogram.types import ReplyKeyboardRemove

from core.keyboards.simple_keyboard import make_simple_keyboard
from core.keyboards.yes_no_inline import make_yes_no_inline


class AskQuestion(StatesGroup):
    choosing_topic = State()
    asking_question = State()


router = Router()

topics = ['Как выбрать подхядящий кружок?',
          'Не могу подключиться к занятиям',
          'Расскажите о ваших кружках',
          'Другой вопрос']


@router.message(Command(commands=['question']))
async def cmd_question(message: Message, state: FSMContext):
    await message.answer(text='Вопрос на какую тему Вы хотели бы задать?',
                         reply_markup=make_simple_keyboard(topics))

    await state.set_state(AskQuestion.choosing_topic)


@router.message(AskQuestion.choosing_topic, F.text.in_(topics))
async def topic_chosen(message: Message, state: FSMContext):
    chosen_topic = message.text

    if chosen_topic == topics[0]:
        await message.answer(text='Бла-бла-бла 1', reply_markup=ReplyKeyboardRemove())
        await state.update_data(topic='1')
        await message.answer(text='Помог ли Вам наш ответ?', reply_markup=make_yes_no_inline())

    elif chosen_topic == topics[1]:
        await message.answer(text='Бла-бла-бла 2', reply_markup=ReplyKeyboardRemove())
        await state.update_data(topic='2')
        await message.answer(text='Помог ли Вам наш ответ?', reply_markup=make_yes_no_inline())

    elif chosen_topic == topics[2]:
        await message.answer(text='Бла-бла-бла 3', reply_markup=ReplyKeyboardRemove())
        await state.update_data(topic='3')
        await message.answer(text='Помог ли Вам наш ответ?', reply_markup=make_yes_no_inline())

    else:
        await message.answer(text='Задайте свой вопрос нашему оператору @itd_reg', reply_markup=ReplyKeyboardRemove())
        await state.clear()


@router.message(AskQuestion.choosing_topic)
async def topic_chosen_incorrectly(message: Message):
    await message.answer(text='Такой темы нет в списке\n\n'
                              'Пожалуйста, выберите один из вариантов ниже:',
                         reply_markup=make_simple_keyboard(topics))


@router.callback_query(AskQuestion.choosing_topic)
async def callbacks_feedback(call: CallbackQuery, state: FSMContext):
    if call.data == 'yes':
        await call.message.edit_text(text='Рады, что смогли Вам помочь!')
        ans = '0'
    else:
        await call.message.edit_text('Жаль, что Вам не помог ответ!\n\n'
                                     'Для дальнейшей помощи можете связаться с @itd_reg')
        ans = '1'

    data = await state.get_data()
    data = (data['topic'], ans)

    conn = sqlite3.connect('core/handlers/questions_stats.db')
    cur = conn.cursor()

    cur.execute('CREATE TABLE IF NOT EXISTS questions (topic, answer)')
    cur.execute(f'INSERT INTO questions (topic, answer) VALUES ("%s", "%s")' % (data[0], data[1]))

    conn.commit()
    cur.close()
    conn.close()

    await call.answer()
