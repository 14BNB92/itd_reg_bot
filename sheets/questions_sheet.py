import sqlite3
from datetime import datetime

import httplib2
import apiclient
from oauth2client.service_account import ServiceAccountCredentials

CREDENTIALS_FILE = 'core/sheets/creds.json'
spreadsheet_id = '16Hwj9PphqE1D0i2IW2-l25jOoDdVKejdXHxr3-mmgMY'

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    CREDENTIALS_FILE,
    ['https://www.googleapis.com/auth/spreadsheets',
     'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)


async def update_table():
    conn = sqlite3.connect('core/handlers/questions_stats.db')
    cur = conn.cursor()

    cur.execute('SELECT * FROM questions ORDER BY topic')
    questions = cur.fetchall()

    topics = {'1': [0, 0], '2': [0, 0], '3': [0, 0]}

    for question in questions:
        topics[question[0]][int(question[1])] += 1

    cur.execute('DROP TABLE IF EXISTS questions')
    cur.execute('CREATE TABLE questions (topic, answer)')
    conn.commit()

    cur.close()
    conn.close()

    day_number = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='Z1'
    ).execute()
    day_number = int(day_number['values'][0][0]) + 3

    today_date = '.'.join(str(datetime.today().date()).split('-')[::-1])

    values = service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {"range": f"A{day_number}:G{day_number}",
                 "majorDimension": "ROWS",
                 "values": [[today_date,
                             str(topics['1'][0]), str(topics['1'][1]),
                             str(topics['2'][0]), str(topics['2'][1]),
                             str(topics['3'][0]), str(topics['3'][1])]]}

            ]
        }
    ).execute()