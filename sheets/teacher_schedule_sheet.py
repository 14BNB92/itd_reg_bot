import httplib2
import apiclient
from oauth2client.service_account import ServiceAccountCredentials

CREDENTIALS_FILE = 'core/sheets/creds.json'
spreadsheet_id = '1rraiatdXa1kpiEgYWub_xFLmMiPWOXd_UVLGWdzsvV8'

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    CREDENTIALS_FILE,
    ['https://www.googleapis.com/auth/spreadsheets',
     'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)


def get_schedule(data_format="COLUMNS"):
    values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='A2:I100000',
        majorDimension=data_format
    ).execute()
    values = values['values']
    return {'ids+names': [values[0], values[1]], 'mon-wen': {0: values[2], 1: values[3], 2: values[4]},
            'thu-sun': {3: values[5], 4: values[6], 5: values[7], 6: values[8]}}


async def update_sheet(ind, day, schedule):
    columns = 'CDEFGHI'

    values = service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            'valueInputOption': 'USER_ENTERED',
            'data': [
                {'range': f'{columns[day]}{ind}',
                 'majorDimension': 'ROWS',
                 'values': [[schedule]]}
            ]
        }
    ).execute()
