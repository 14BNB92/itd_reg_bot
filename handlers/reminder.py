from datetime import datetime, date, timedelta
from aiogram import Bot

from core.sheets.students_sheet import get_data, transfer_group
from core.sheets.teacher_schedule_sheet import get_schedule
from core.keyboards.yes_no_inline import make_yes_no_inline


async def make_reminder_dict():
    data = get_data()
    ids = data[0][1:]
    names = data[1][1:]
    courses = data[6][1:]
    reminder_dict = dict()

    for i in range(len(courses)):
        course = courses[i]
        course = str(course).split('\n')
        if course == ['-']:
            continue
        else:
            expiring_courses = ''
            for x in course:
                x = x.split()
                course_name = x[0]
                days = 0

                expiration_date = datetime.strptime(x[1][1:-1], '%d.%m.%Y').date()
                today_date = date.today()

                if expiration_date - timedelta(days=7) == today_date:
                    days = 'через 7 дней'

                elif expiration_date - timedelta(days=3) == today_date:
                    days = 'через 3 дня'

                elif expiration_date == today_date:
                    days = 'сегодня'

                elif expiration_date + timedelta(days=1) == today_date:
                    await transfer_group(ids[i], names[i], course_name)

                if days != 0:
                    expiring_courses += f'Кружок: {course_name} истекает {days}\n'

            if len(expiring_courses) > 0:
                if ids[i] in reminder_dict:
                    reminder_dict[ids[i]] += [[names[i], expiring_courses]]
                else:
                    reminder_dict[ids[i]] = [[names[i], expiring_courses]]

    return reminder_dict


async def send_reminder(bot: Bot):
    recipient_list = await make_reminder_dict()
    if len(recipient_list) != 0:
        for recipient_id in recipient_list:
            recipient = recipient_list[recipient_id]
            text = 'Здравствуйте!\n' \
                   'Истекает подписка для Ваших детей\n'
            for child in recipient:
                text += f'Имя: <b>{child[0]}</b>\n{child[1]}\n'

            await bot.send_message(chat_id=recipient_id, text=text, parse_mode='html')


async def ask_confirmation(bot: Bot):
    data = get_schedule()
    ids = data['ids+names'][0]
    names = data['ids+names'][1]
    weekday = datetime.today().weekday()
    weekdays = {0: 'понедельник', 1: 'вторник', 2: 'среда', 3: 'четверг', 4: 'пятница', 5: 'суббота', 6: 'воскресенье'}

    if weekday == 0:
        schedule = data['mon-wen']
    else:
        schedule = data['thu-sun']

    for i in range(len(ids)):
        teacher_id = ids[i]
        name = names[i]
        teacher_schedule = dict()

        for day in schedule:
            teacher_schedule[day] = schedule[day][i]

        flag = 0
        for day in teacher_schedule:
            if teacher_schedule[day] != '-':
                flag = 1
                break

        if flag == 1:
            await bot.send_message(chat_id=teacher_id,
                                   text=f'Здравствуйте, {name}!\nСможете ли Вы провести следующие занятия:')

            for day in teacher_schedule:
                groups = teacher_schedule[day].split('\n')
                groups = [x.split() for x in groups]

                for lesson in groups:
                    if lesson == ['-']:
                        continue
                    group_name = lesson[0]
                    lesson_time = lesson[1]
                    lesson_day = weekdays[day]

                    await bot.send_message(chat_id=teacher_id,
                                           text=f'Группа: {group_name}\n'
                                                f'Время занятия: {lesson_day} {lesson_time}',
                                           reply_markup=make_yes_no_inline([
                                               f'{teacher_id}@@{day}@@{lesson_time}@@{group_name}@@yes',
                                               f'{teacher_id}@@{day}@@{lesson_time}@@{group_name}@@no'
                                           ]))

