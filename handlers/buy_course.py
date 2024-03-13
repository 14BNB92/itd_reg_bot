import requests
from random import randint
from hashlib import sha256

from config import PAYMENT_PASSWORD, TERMINAL_KEY
from core.keyboards.simple_inline import make_simple_inline
from core.keyboards.yes_no_inline import make_yes_no_inline
from core.sheets.groups_sheet import get_info
from core.sheets.students_sheet import add_group, get_data
from core.handlers.register_user import not_registered

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

router = Router()
ORDER_INFO = None


class BuyCourse(StatesGroup):
    choosing_child = State()
    deciding_on_bonuses = State()
    choosing_group_type = State()
    entering_mail = State()
    choosing_group = State()
    choosing_rate = State()


def check_group(group: str):
    data = get_info()

    if group in data['group'][0] or group in data['course'][0]:
        return True

    return False


def select_children(user_id):
    data = get_data()
    ids = data[0][1:]
    names = data[1][1:]

    children = []
    for i in range(len(ids)):
        if user_id == int(ids[i]):
            children.append([names[i], names[i]])

    return children


@router.message(Command(commands=['pay']),
                lambda message: not_registered(message.from_user.id))
async def cmd_pay_if_not_registered(message: Message):
    await message.answer(text='Для оплаты кружка необхоимо заегистрировать хотя бы одного ребенка!\n'
                              'Используйте команду /register', reply_markup=ReplyKeyboardRemove())


@router.message(Command(commands=['pay']))
async def cmd_pay(message: Message, state: FSMContext):
    await message.answer(text="Здравствуйте!\n"
                              "Выберите ребенка, курс которого Вы хотите оплатить:",
                         reply_markup=make_simple_inline(select_children(message.from_user.id)))

    await state.set_state(BuyCourse.choosing_child)
    await state.update_data(user_id=message.from_user.id)


@router.message(BuyCourse.entering_mail, F.text,
                lambda message: '@yandex.ru' in message.text or '@gmail.com' in message.text
                                or '@mail.ru' in message.text)
async def mail_entered(message: Message, state: FSMContext):
    await state.update_data(email=message.text)
    data = await state.get_data()

    await message.answer(text='Почта принята!\n'
                              f'Теперь введите название {data["str_group_type"]}, который хотите оплатить:')

    await state.set_state(BuyCourse.choosing_group)


@router.message(BuyCourse.entering_mail)
async def mail_entered_incorrectly(message: Message):
    await message.answer(text='Почта введена некорректно! '
                              'Попробуйте, пожалуйста, еще раз:')


@router.message(BuyCourse.choosing_group, F.text,
                lambda message: check_group(message.text))
async def group_chosen(message: Message, state: FSMContext):
    global ORDER_INFO
    group_type_and_bonuses = await state.get_data()
    group_type = group_type_and_bonuses['group_type']
    bonuses_used = group_type_and_bonuses['bonuses_used']
    bonuses = group_type_and_bonuses['bonuses']
    group = message.text
    data = get_info()
    data = data[group_type]
    ind = data[0].index(group)

    await state.update_data(group=group)

    if group_type == 'course':
        price = int(data[1][ind])
        order_id = f"{randint(10 ** 5, 10 ** 6 - 1)}{group}"
        email = await state.get_data()
        email = email['email']

        if bonuses_used:
            if bonuses >= price:
                used_bonuses = price - 1
                price = 1
            else:
                used_bonuses = bonuses
                price -= bonuses
        else:
            used_bonuses = 0

        price *= 100

        await state.update_data(link=data[2][ind], days=0, used_bonuses=used_bonuses, price=price // 100)

        token_str = f"{price}{group}{order_id}{PAYMENT_PASSWORD}{TERMINAL_KEY}"

        request_data = {
            "TerminalKey": TERMINAL_KEY,
            "Amount": price,
            "OrderId": order_id,
            "Description": group,
            "Receipt": {
                "Items": [
                    {
                        "Name": group,
                        "Price": price,
                        "Quantity": 1,
                        "Amount": price,
                        "Tax": "none"
                    },
                ],
                "Email": email,
                "Taxation": "usn_income"
            },
            "Token": sha256(bytes(token_str, "utf-8")).hexdigest()
        }

        response = requests.post(url="https://securepay.tinkoff.ru/v2/Init/",
                                 headers={"Content-Type": "application/json"},
                                 json=request_data)
        print(response.text)
        response = response.json()

        ORDER_INFO = {
            "TerminalKey": TERMINAL_KEY,
            "PaymentId": response['PaymentId'],
        }

        token_dict = sorted(ORDER_INFO)
        token_dict += ["Password"]
        token_dict = sorted(token_dict)
        token = ''

        for key in token_dict:
            if key == "Password":
                token += PAYMENT_PASSWORD
            else:
                token += str(ORDER_INFO[key])

        ORDER_INFO["Token"] = sha256(bytes(token, 'utf-8')).hexdigest()

        payment_url = response['PaymentURL']

        str_group_type = 'интенсива'

        await message.answer(text=f"Оплата {str_group_type} {group}. "
                                  f"Цена: {price // 100} RUB\n\n"
                                  f"После оплаты ОБЯЗАТЕЛЬНО нажмите на кнопку 'Подтвердить оплату'",
                             reply_markup=make_simple_inline([['Оплатить', 'None', payment_url, request_data],
                                                              ['Проверить оплату', 'check_payment']]))

    else:
        prices = data[1][ind].split('\n')
        prices = [prices[0]] + [x.split() for x in prices[1:]]
        keyboard = [[f'{prices[0]} (месяц)', f'{prices[0]}_month']]
        for x in prices[1:]:
            keyboard += [[f'{x[0]} ({x[1][1:-1]} дней)', f'{x[0]}_{x[1][1:-1]}']]

        await message.answer(text='Теперь выберите тариф, по которому хотите оплатить круржок',
                             reply_markup=make_simple_inline(keyboard))

        await state.set_state(BuyCourse.choosing_rate)


@router.message(BuyCourse.choosing_group, F.text)
async def group_chosen_incorrectly(message: Message):
    await message.answer(text='Некорректное название кружка/интенсива! Пожалуйста, попробуйте еще раз:')


@router.callback_query(BuyCourse.choosing_child)
async def child_chosen(call: CallbackQuery, state: FSMContext):
    await state.update_data(child_name=call.data)

    data = get_data()
    ids = data[0][1:]
    names = data[1][1:]
    bonuses = data[7][1:]
    child_data = await state.get_data()
    user_id = child_data['user_id']

    ind = 0
    for i in range(len(ids)):
        if ids[i] == str(user_id) and names[i] == call.data:
            ind = i
            break

    await state.update_data(bonuses=int(bonuses[ind]))

    if bonuses[ind] != '0':
        await call.message.edit_text(text=f'За выбранным ребенком закреплено {bonuses[ind]} бонусных рублей! '
                                          f'Желаете их использовать?',
                                     reply_markup=make_yes_no_inline())

        await state.set_state(BuyCourse.deciding_on_bonuses)

    else:
        await call.message.edit_text(text='Отлично!\n'
                                          'Теперь Выберите, что Вы хотите оплатить:',
                                     reply_markup=make_simple_inline([['Кружок', 'group'], ['Интенсив', 'course']]))

        await state.update_data(bonuses_used=False)

        await state.set_state(BuyCourse.choosing_group_type)

    await call.answer()


@router.callback_query(BuyCourse.deciding_on_bonuses, lambda call: call.data in ['yes', 'no'])
async def bonuses_decided(call: CallbackQuery, state: FSMContext):
    if call.data == 'yes':
        bonuses_used = True
        additional_text = 'бонусы будут использованы'
    else:
        bonuses_used = False
        additional_text = 'бонусы не будут использованы'

    await call.message.edit_text(text=f'Хорошо, {additional_text}!\n'
                                      'Теперь Выберите, что Вы хотите оплатить:',
                                 reply_markup=make_simple_inline([['Кружок', 'group'], ['Интенсив', 'course']]))

    await state.update_data(bonuses_used=bonuses_used)
    await state.set_state(BuyCourse.choosing_group_type)

    await call.answer()


@router.callback_query(BuyCourse.choosing_group_type,
                       lambda call: call.data in ['group', 'course'])
async def group_type_chosen(call: CallbackQuery, state: FSMContext):
    if call.data == 'group':
        str_group_type = 'кружка'
    else:
        str_group_type = 'интенсива'

    await state.update_data(group_type=call.data, str_group_type=str_group_type)

    await call.message.edit_text(text=f'Теперь введите свою почту для получения чека:')

    await state.set_state(BuyCourse.entering_mail)
    await call.answer()


@router.callback_query(BuyCourse.choosing_rate, lambda call: call.data != 'check_payment')
async def rate_chosen(call: CallbackQuery, state: FSMContext):
    global ORDER_INFO

    data = await state.get_data()
    group = data['group']
    bonuses = data['bonuses']
    bonuses_used = data['bonuses_used']
    price_data = call.data.split('_')
    price = int(str(price_data[0]))
    email = data['email']
    if price_data[1] != 'month':
        days = int(price_data[1])
    else:
        days = 'month'

    if bonuses_used:
        if bonuses >= price:
            used_bonuses = price - 1
            price = 1
        else:
            used_bonuses = bonuses
            price -= bonuses
    else:
        used_bonuses = 0

    price *= 100

    await state.update_data(days=days, used_bonuses=used_bonuses, price=price // 100)

    order_id = f"{randint(10 ** 5, 10 ** 6 - 1)}{group}"

    token_str = f"{price}{group}{order_id}{PAYMENT_PASSWORD}{TERMINAL_KEY}"

    request_data = {
        "TerminalKey": TERMINAL_KEY,
        "Amount": price,
        "OrderId": order_id,
        "Description": group,
        "Receipt": {
            "Items": [
                {
                    "Name": group,
                    "Price": price,
                    "Quantity": 1,
                    "Amount": price,
                    "Tax": "none"
                },
            ],
            "Email": email,
            "Taxation": "usn_income"
        },
        "Token": sha256(bytes(token_str, "utf-8")).hexdigest()
    }

    response = requests.post(url="https://securepay.tinkoff.ru/v2/Init/",
                             headers={"Content-Type": "application/json"},
                             json=request_data)

    response = response.json()

    ORDER_INFO = {
        "TerminalKey": TERMINAL_KEY,
        "PaymentId": response['PaymentId'],
    }

    token_dict = sorted(ORDER_INFO)
    token_dict += ["Password"]
    token_dict = sorted(token_dict)
    token = ''

    for key in token_dict:
        if key == "Password":
            token += PAYMENT_PASSWORD
        else:
            token += str(ORDER_INFO[key])

    ORDER_INFO["Token"] = sha256(bytes(token, 'utf-8')).hexdigest()

    payment_url = response['PaymentURL']

    str_group_type = 'кружка'

    await call.message.edit_text(text=f"Оплата {str_group_type} {group}. "
                                      f"Цена: {price // 100} RUB\n\n"
                                      f"После оплаты ОБЯЗАТЕЛЬНО нажмите на кнопку 'Подтвердить оплату'",
                                 reply_markup=make_simple_inline([['Оплатить', 'None', payment_url, request_data],
                                                                  ['Проверить оплату', 'check_payment']]))
    await call.answer()


@router.callback_query(lambda call: call.data == 'check_payment')
async def check_payment(call: CallbackQuery, state: FSMContext, bot: Bot):
    global ORDER_INFO
    if ORDER_INFO is None:
        await call.message.answer(text='Сейчас у Вас нет активного чека на оплату!\n'
                                       'Используйте команду /pay чтобы провести оплату')
    else:
        response = requests.post(url='https://securepay.tinkoff.ru/v2/GetState/',
                                 headers={"Content-Type": "application/json"},
                                 json=ORDER_INFO)
        response = response.json()
        payment_status = response["Status"]
        payment_id = response["PaymentId"]

        if payment_status == "NEW":
            await call.message.answer(text='Чек на оплату создан и доступен по ссылке. Нажмите на кнопку "Оплатить"')

        elif payment_status == "FORM_SHOWED":
            await call.message.answer(text='Похоже, Вы не завершили оплату. '
                                           'Переведите средства и потом нажмите на кнопку подтверждения')

        elif payment_status == "CONFIRMED":
            await call.message.edit_text("Платеж проведен успешно!✅")

            data = await state.get_data()
            await add_group(data['user_id'], data['child_name'], data["group"], data["group_type"], data['days'],
                            data['bonuses_used'], data['used_bonuses'], data['bonuses'] - data['used_bonuses'],
                            data['price'])

            token = f'{PAYMENT_PASSWORD}{payment_id}{TERMINAL_KEY}'

            if data['group_type'] == 'course':
                await bot.send_message(chat_id=data['user_id'],
                                       text=f'{data["link"]}')

            else:
                pass

            receipt = {
                "TerminalKey": TERMINAL_KEY,
                "PaymentId": payment_id,
                "Receipt": {
                    "FfdVersion": "1.2",
                    "Taxation": "usn_income",
                    "Email": data['email'],
                    "Items": [
                        {
                            "Name": data['group'],
                            "Price": data['price'] * 100,
                            "Quantity": 1,
                            "Amount": data['price'] * 100,
                            "Tax": "none",
                            "PaymentMethod": "full_prepayment",
                            "PaymentObject": "service",
                            "MeasurementUnit": "-"
                        }
                    ]
                },
                "Token": sha256(bytes(token, "utf-8")).hexdigest()
            }

            response = requests.post(url='https://securepay.tinkoff.ru/v2/SendClosingReceipt/',
                                     headers={"Content-Type": "application/json"},
                                     json=receipt)
            print(response, response.text)

            await state.clear()

        elif payment_status == "DEADLINE_EXPIRED":
            await call.message.edit_text("Истек срок ожидания оплаты! "
                                         "Для повторной попытки используйте команду /pay")
            await state.clear()

        elif payment_status == "REJECTED":
            await call.message.edit_text(text="Упс, что-то пошло не так! "
                                              "Для повторной попытки используйте команду /pay")
            await state.clear()

    await call.answer()
