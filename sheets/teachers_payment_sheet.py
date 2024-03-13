import httplib2
import apiclient
from oauth2client.service_account import ServiceAccountCredentials

CREDENTIALS_FILE = 'core/sheets/creds.json'
spreadsheet_id = '14ZCherCjavlQu48Vl0Kh7L4ZYqR8CEJLls0sUt1QkhM'

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    CREDENTIALS_FILE,
    ['https://www.googleapis.com/auth/spreadsheets',
     'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)


def check_payment_amount(teacher_name):
    values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='B7:G1000',
        majorDimension='COLUMNS'
    ).execute()

    data = values['values']
    names = data[0]
    payments = data[5]
    ind = names.index(teacher_name)

    return payments[ind]
