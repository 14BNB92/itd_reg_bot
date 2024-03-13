import httplib2
import apiclient
from oauth2client.service_account import ServiceAccountCredentials

CREDENTIALS_FILE = 'core/sheets/creds.json'
spreadsheet_id = '1YaTi-1QgjIGVQbCUcR7FZsUI99W9arlQuVUNyi9KC_o'

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    CREDENTIALS_FILE,
    ['https://www.googleapis.com/auth/spreadsheets',
     'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)


def get_info():
    values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='A2:E1000000',
        majorDimension='COLUMNS'
    ).execute()

    values = values['values']

    return {'group': [values[0], values[1]], 'course': [values[2], values[3], values[4]]}
