import httplib2
import apiclient
from oauth2client.service_account import ServiceAccountCredentials

CREDENTIALS_FILE = 'core/sheets/creds.json'
spreadsheet_id = '1rmtRV7wyI2Xc3IflaBoqQL8XVz49XQYibu-q7R2AcIk'

credentials = ServiceAccountCredentials.from_json_keyfile_name(
    CREDENTIALS_FILE,
    ['https://www.googleapis.com/auth/spreadsheets',
     'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)


def get_mail_data(data_format="COLUMNS"):
    values = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range='A1:C100000',
        majorDimension=data_format
    ).execute()

    return values['values']


async def add_child(user_id, name):
    data = get_mail_data()

    ids = data[0]
    names = data[1]

    if str(user_id) in ids:
        ind = ids.index(str(user_id))
        finite_names = names[ind] + '\n' + name
        add_id = False
    else:
        ind = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range='Z1'
        ).execute()
        ind = int(ind['values'][0][0]) + 1
        finite_names = name
        add_id = True

    if add_id:
        values = service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={
                'valueInputOption': 'USER_ENTERED',
                'data': [
                    {'range': f'A{ind + 1}:C{ind + 1}',
                     'majorDimension': 'ROWS',
                     'values': [[user_id, finite_names, '-']]}
                ]
            }
        ).execute()

    else:
        values = service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={
                'valueInputOption': 'USER_ENTERED',
                'data': [
                    {'range': f'B{ind + 1}',
                     'majorDimension': 'ROWS',
                     'values': [[finite_names]]}
                ]
            }
        ).execute()


async def reset_texts():
    data = get_mail_data()
    ids = data[0]

    values = service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            'valueInputOption': 'USER_ENTERED',
            'data': [
                {'range': f'C2:C{len(ids)}',
                 'majorDimension': 'COLUMNS',
                 'values': [['-'] * (len(ids) - 1)]}
            ]
        }
    ).execute()
