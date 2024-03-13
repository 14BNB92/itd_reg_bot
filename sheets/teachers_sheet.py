import httplib2
import apiclient
from oauth2client.service_account import ServiceAccountCredentials

CREDENTIALS_FILE = 'core/sheets/creds.json'
spreadsheet_id = '1uN3RCsGScKcYs8Vr0wNs1aop0eLxMLo7k26350dIyok'

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    CREDENTIALS_FILE,
    ['https://www.googleapis.com/auth/spreadsheets',
     'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)


def get_teacher_data(data_format="COLUMNS"):
    values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='A1:C10000',
        majorDimension=data_format
    ).execute()

    return values['values']

