import calendar
from datetime import datetime, timedelta
from core.sheets.payments_sheet import add_transaction
from core.sheets.mail_sheet import add_child

import httplib2
import apiclient
from oauth2client.service_account import ServiceAccountCredentials

CREDENTIALS_FILE = 'core/sheets/creds.json'
spreadsheet_id = '1OWXlBPAYBM9fW801VExwR2NrgV0hsqRIiMOYLibVMm8'

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    CREDENTIALS_FILE,
    ['https://www.googleapis.com/auth/spreadsheets',
     'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)


def get_data(data_format="COLUMNS"):
    values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='A1:H100000',
        majorDimension=data_format
    ).execute()

    return values['values']


async def register_user(user_id, name, birthday, grade, disciplines):
    student_number = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='Z1'
    ).execute()
    student_number = int(student_number['values'][0][0])
    values = service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {"range": f"A{student_number}:H{student_number}",
                 "majorDimension": "ROWS",
                 "values": [[user_id, name, birthday, grade, disciplines, '-', '-', 0]]}
            ]
        }
    ).execute()

    await add_child(user_id, name)


async def add_group(user_id, child_name, group, group_type, days, bonuses_used, used_bonuses, bonuses_left, amount):
    ind = 1
    data = get_data()
    user_ids = data[0][1:]
    names = data[1][1:]

    for i in range(len(user_ids)):
        if user_id == int(user_ids[i]) and child_name == names[i]:
            ind = i + 1
            break

    if group_type == 'course':
        courses = data[5][ind]
        column = 'F'
        if courses == '-':
            courses = group
        else:
            if group not in data[5][ind]:
                courses += f'\n{group}'

    else:
        courses = data[6][ind]

        column = 'G'
        if days == 'month':
            expiration_date = datetime.today().date()
            days_in_month = calendar.monthrange(expiration_date.year, expiration_date.month)[1]
            expiration_date += timedelta(days=days_in_month)
        else:
            expiration_date = datetime.today().date() + timedelta(days=days)
        additional_days = timedelta(days=0)

        if courses != '-':
            groups = courses.split('\n')
            groups = [x.split() for x in groups]
            courses = ''

            for x in groups:
                if x[0] == group:
                    additional_days = datetime.strptime(x[1][1:-1], '%d.%m.%Y').date() - datetime.today().date()
                else:
                    courses += f'{x[0]} {x[1]}'

        expiration_date += additional_days

        expiration_date = '.'.join(str(expiration_date).split('-')[::-1])

        if courses == '-' or courses == '':
            courses = f'{group} ({expiration_date})'
        else:
            courses += f'\n{group} ({expiration_date})'

        group = f'{group} ({expiration_date})'

    values = service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {"range": f"{column}{ind + 1}",
                 "majorDimension": "ROWS",
                 "values": [[courses]]}
            ]
        }
    ).execute()

    if bonuses_used:
        values = service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={
                "valueInputOption": "USER_ENTERED",
                "data": [
                    {"range": f"H{ind + 1}",
                     "majorDimension": "ROWS",
                     "values": [[bonuses_left]]}
                ]
            }
        ).execute()

    await add_transaction(user_id, child_name, group, amount, used_bonuses)


async def transfer_group(user_id, name, group):
    data = get_data()
    ids = data[0]
    names = data[1]
    ind = 0

    for i in range(len(ids)):
        if ids[i] == str(user_id) and names[i] == name:
            ind = i
            break
    print(ind, name, user_id)
    previous_groups = data[5][ind]
    current_groups_data = data[6][ind].split('\n')
    current_groups = ''

    if previous_groups == '-':
        previous_groups = group
    else:
        if group not in previous_groups:
            previous_groups += f'\n{group}'

    for course in current_groups_data:
        course = course.split()
        name = course[0]
        expiration_date = course[1][1:-1]

        if name != group:
            current_groups += f'{name} ({expiration_date})'

    if current_groups == '':
        current_groups = '-'

    values = service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {"range": f"F{ind + 1}:G{ind + 1}",
                 "majorDimension": "ROWS",
                 "values": [[previous_groups, current_groups]]}
            ]
        }
    ).execute()


async def update_grades():
    data = get_data()
    ids = data[0][1:]
    names = data[1][1:]
    birthdays = data[2][1:]
    grades = [int(x) for x in data[3][1:]]
    disciplines = data[4][1:]
    previous_groups = data[5][1:]
    current_groups = data[6][1:]
    bonuses = data[7][1:]
    students = []

    for i in range(len(ids)):
        if grades[i] != 11:
            students.append([ids[i], names[i], birthdays[i], grades[i] + 1, disciplines[i], previous_groups[i],
                             current_groups[i], bonuses[i]])

    students += [[''] * 8] * 10000
    ind = len(students)

    values = service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {"range": f"A2:H{ind + 1}",
                 "majorDimension": "ROWS",
                 "values": students}
            ]
        }
    ).execute()
