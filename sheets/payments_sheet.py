import httplib2
import apiclient
from oauth2client.service_account import ServiceAccountCredentials

from datetime import datetime

CREDENTIALS_FILE = 'core/sheets/creds.json'
spreadsheet_id = '13zbI5OWWTGGp5Z_sMtqGm_XVtCvOzvjo_hmZSyKgSTE'

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    CREDENTIALS_FILE,
    ['https://www.googleapis.com/auth/spreadsheets',
     'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)


async def add_transaction(user_id, child_name, group, amount, used_bonuses):
    transaction_number = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='Z1'
    ).execute()
    transaction_number = int(transaction_number['values'][0][0])

    today_date = '.'.join(str(datetime.today().date()).split('-')[::-1])

    values = service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {"range": f"A{transaction_number}:F{transaction_number}",
                 "majorDimension": "ROWS",
                 "values": [[user_id, child_name, group, amount, used_bonuses, today_date]]}
            ]
        }
    ).execute()
