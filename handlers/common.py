from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery

router = Router()


@router.message(Command(commands='start'))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(text='Здравствуйте!\nЭто бот команды онлайн-школы "И так далее..."\n'
                              'Для дальнейшего использования Вам необходимо добавить ребенка!\n\n'
                              'Используйте команду /register\n'
                              'Если хотите узнать остальной функционал бота, используйте команду /help')


@router.message(Command(commands=['help']))
async def cmd_help(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(text='Что может данный бот? Для использования Вам доступны следующие команды:\n'
                              '/register — зарегистрировать ребенка в нашей системе\n'
                              '/question — задать вопрос\n'
                              '/pay — оплатить кружок/интенсив\n'
                              '/cancel — отменить действие\n\n'
                              'Также бот будет присылать Вам напоминания об оплате кружков. Приятного использования!')


@router.message(Command(commands=['cancel']))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        text="Действие отменено",
        reply_markup=ReplyKeyboardRemove())


@router.message(Command(commands=['id']))
async def cmd_id(message: Message):
    await message.answer(text=str(message.chat.id))
