import httplib2
import apiclient
from oauth2client.service_account import ServiceAccountCredentials

CREDENTIALS_FILE = 'core/sheets/creds.json'
spreadsheet_id = '1fen0n1rpNixjSJHSFrz-Q7uAh1Ra7y2RqNGgrCOX7dg'

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    CREDENTIALS_FILE,
    ['https://www.googleapis.com/auth/spreadsheets',
     'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)


def get_admins_list(data_format="COLUMNS"):
    values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='A1:B100000',
        majorDimension=data_format
    ).execute()

    values = values['values']
    admin_ids = values[0]
    admin_names = values[1]
    if len(admin_ids) > 1:
        admin_ids = [int(x) for x in admin_ids[1:]]

    return admin_ids
