from google.oauth2 import service_account
from googleapiclient.discovery import build
from config import *


# Functions for Whatsapp Scraper
def setup_sheets_api():
    creds = service_account.Credentials.from_service_account_info(json_info, scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    return service.spreadsheets()

def send_data_to_sheets(values, sheets , id ):
    body = {'values': values}
    result = sheets.values().append(
        spreadsheetId=id,
        range=RANGE_NAME,
        valueInputOption='USER_ENTERED',
        insertDataOption='INSERT_ROWS',
        body=body
    ).execute()
    return result

def read_group_names_from_sheets(sheets):
    sheet_range = 'Sheet2!A:D'
    result = sheets.values().get(spreadsheetId=SPREADSHEET1_ID, range=sheet_range).execute()
    values = result.get('values', [])
    group_names = [value[0] for value in values[1:] if value] if values else []
    return group_names

def read_data_from_sheets(sheets):
    sheet_range = 'Sheet1!A:E'
    result = sheets.values().get(spreadsheetId=SPREADSHEET2_ID, range=sheet_range).execute()
    values = result.get('values', [])
    message_data = values[1:] if len(values) > 1 else []
    return message_data

def clear_sheet_except_header(sheets, spreadsheet_id):
    sheet_metadata = sheets.get(spreadsheetId=spreadsheet_id).execute()
    properties = sheet_metadata.get('sheets', [])[0].get('properties')
    sheet_id = properties['sheetId']
    batch_clear_request = {
        'requests': [
            {
                'updateCells': {
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': 1 
                    },
                    'fields': 'userEnteredValue'
                }
            }
        ]
    }
    sheets.batchUpdate(spreadsheetId=spreadsheet_id, body=batch_clear_request).execute()


#Functions for Linkedin Scraper

def get_urls_and_statuses_from_sheet(sheets):
    result = sheets.values().get(
        spreadsheetId=SPREADSHEET1_ID,
        range='Sheet1!H:I'  # Link column is H, Status column is I
    ).execute()
    values = result.get('values', [])
    if not values:
        print('No data found in the sheet.')
        return []
    return [(row[0], row[1] if len(row) > 1 else "") for row in values[1:] if row]


def update_status(row_index, status , sheets):
    range_name = f'Sheet1!I{row_index}'
    body = {
        'values': [[status]]
    }
    result = sheets.values().update(
        spreadsheetId=SPREADSHEET1_ID, range=range_name,
        valueInputOption='USER_ENTERED', body=body).execute()
    print(f"Status updated for row {row_index}: {status}")


def save_to_google_sheets(data, sheets):
    range_name = 'Sheet3!A1:G1'  # Start from A1 in Sheet3
    sheet = sheets.get(spreadsheetId=SPREADSHEET1_ID, range=range_name).execute()
    header_exists = len(sheet.get('values', [])) > 0
    headers = ["Name", "Job Title", "Profile Link", "Info", "More info", "OpenAI", "Original URL"]
    values = []
    if not header_exists:
        values.append(headers)
    values.append(list(data.values()))
    body = {'values': values}
    result = sheets.values().append(
        spreadsheetId=SPREADSHEET1_ID, range=range_name,
        valueInputOption='USER_ENTERED', insertDataOption='INSERT_ROWS', body=body).execute()
    print(f"{result.get('updates').get('updatedCells')} cells appended.")


sheets = setup_sheets_api()


