import logging
import os

import gspread
from flask import jsonify
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
load_dotenv()
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

def store_in_google_sheets(objects, sheet_id, work_sheet_name,selected_fields):
    """Store the retrieved HubSpot object data in Google Sheets."""
    client = get_gspread_client()
    try:
        # Open the Google Sheet by its ID
        sheet = client.open_by_key(sheet_id)

        # Try to access the specified worksheet
        try:
            worksheet = sheet.worksheet(work_sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            print("Available worksheets:", [ws.title for ws in sheet.worksheets()])
            print(f"Worksheet '{work_sheet_name}' not found. Creating a new worksheet.")
            worksheet = sheet.add_worksheet(title=work_sheet_name, rows="100", cols="20")
            print(f"Worksheet '{work_sheet_name}' created.")
    except Exception as e:
        print(f"Error accessing the Google Sheet: {e}")
        return f"Error accessing the Google Sheet: {e}"

    # sheet = client.open_by_key(sheet_id)
    # worksheet = sheet.worksheet(work_sheet_name)
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
    # Create headers in Google Sheets based on selected fields
    rows = [['id'] + selected_fields]  # The first row will be the header row with field names

    # Add data rows based on selected fields
    for obj in objects:
        obj_id =obj.get("id",'')
        properties = obj.get('properties', {})
        row = [obj_id] +[properties.get(field, '') for field in selected_fields]  # Get field value or '' if not present
        rows.append(row)

    # Check the structure of `rows` before sending to the sheet
    print("Rows to be inserted:", rows)  # Debugging line to inspect the rows structure

    # Insert data into the Google Sheet
    try:
        worksheet.update(range_name="A1", values=rows)  # Update the range with values
        print("Data successfully written to the Google Sheet.")
    except Exception as e:
        print(f"Error while updating Google Sheet: {e}")
        return f"Error while updating Google Sheet: {e}"

    return jsonify({"message":"Data successfully written to the Google Sheet.","sheet_url":sheet_url})


def share_google_sheet(sheet_id, list_email):
    """Share the Google Sheet with a specific email address."""
    creds = Credentials.from_service_account_file(service_account_file_path)
    service = build('drive', 'v3', credentials=creds)

    for email in list_email:
        permission_body = {
            'role': 'writer',
            'type': 'user',
            'emailAddress': email
        }
        try:
            service.permissions().create(fileId=sheet_id, body=permission_body, fields='id').execute()
            logging.info(f"Successfully shared sheet {sheet_id} with {email}")
        except HttpError as error:
            logging.error(f"An error occurred while sharing the sheet with {email}: {error}")

    # permission_body = {
    #     'role': 'writer',
    #     'type': 'user',
    #     'emailAddress': email
    # }
    # try:
    #     service.permissions().create(fileId=sheet_id, body=permission_body, fields='id').execute()
    #     logging.info(f"Successfully shared sheet {sheet_id} with {email}")
    # except HttpError as error:
    #     logging.error(f"An error occurred while sharing the sheet: {error}")