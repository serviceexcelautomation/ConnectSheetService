import os

from googleapiclient.discovery import build
import logging
from googleapiclient.errors import HttpError
import json
import gspread
from google.oauth2.service_account import Credentials

service_account_file_path = os.getenv("service_account_file_path")
# Google Sheets API setup
def get_gspread_client():
    """Authenticate and return a gspread client."""
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(service_account_file_path, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client

def create_google_sheet(sheet_name):
    """Create a new Google Sheet and return its ID."""
    creds = Credentials.from_service_account_file(service_account_file_path)
    service = build('sheets', 'v4', credentials=creds)
    spreadsheet_body = {
        'properties': {
            'title': sheet_name
        }
    }
    try:
        spreadsheet = service.spreadsheets().create(body=spreadsheet_body, fields='spreadsheetId').execute()
        sheet_id = spreadsheet.get('spreadsheetId')
        logging.info(f"Created new sheet with ID: {sheet_id}")
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
        logging.info(f"Access your sheet at: {sheet_url}")
        return sheet_id
    except Exception as e:
        logging.error(f"An error occurred while creating the sheet: {e}")
        return None

def store_in_google_sheets(objects, sheet_id, selected_fields):
    """Store the retrieved HubSpot object data in Google Sheets."""
    client = get_gspread_client()
    sheet = client.open_by_key(sheet_id).sheet1

    # Create headers in Google Sheets based on selected fields
    rows = [selected_fields]  # The first row will be the header row with field names

    # Add data rows based on selected fields
    for obj in objects:
        properties = obj.get('properties', {})
        row = [properties.get(field, '') for field in selected_fields]  # Get field value or '' if not present
        rows.append(row)
    print(rows)
    # Insert data into the Google Sheet
    sheet.update(range_name ="A1",values=rows)
    print("Data successfully written to the Google Sheet.")
    return "Data successfully written to the Google Sheet."

def share_google_sheet(sheet_id, email):
    """Share the Google Sheet with a specific email address."""
    creds = Credentials.from_service_account_file(service_account_file_path)
    service = build('drive', 'v3', credentials=creds)
    # list of e-mails
    # for email in emails:
    #     permission_body = {
    #         'role': 'writer',
    #         'type': 'user',
    #         'emailAddress': email
    #     }
    #     try:
    #         service.permissions().create(fileId=sheet_id, body=permission_body, fields='id').execute()
    #         logging.info(f"Successfully shared sheet {sheet_id} with {email}")
    #     except HttpError as error:
    #         logging.error(f"An error occurred while sharing the sheet with {email}: {error}")

    permission_body = {
        'role': 'writer',
        'type': 'user',
        'emailAddress': email
    }
    try:
        service.permissions().create(fileId=sheet_id, body=permission_body, fields='id').execute()
        logging.info(f"Successfully shared sheet {sheet_id} with {email}")
    except HttpError as error:
        logging.error(f"An error occurred while sharing the sheet: {error}")