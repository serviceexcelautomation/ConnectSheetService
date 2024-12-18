# hubspot_integration/hubspot_api.py

import logging
import os

import requests
from dotenv import load_dotenv
from flask import redirect, json, jsonify

from backend.common.access_token.redis_connection import RedisConnection
from backend.common.google_sheet.google_sheet_service import create_google_sheet, share_google_sheet, \
    store_in_google_sheets

# Load environment variables
load_dotenv()

HUBSPOT_API_URL = os.getenv("HUBSPOT_API_URL")
HOME_PAGE_URL=os.getenv("HOME_PAGE_URL")

redis_connection = RedisConnection()

def get_access_token(email):
    """Retrieve the access token from the session."""
    access_token = redis_connection.hget('user_tokens', email)
    return access_token

def get_user_email():
    # Implement this function to get the user's email or ID from HubSpot using the access token
    return "user@example.com"

# To get hubspot tables
def fetch_hubspot_tables():
    print("hubspot table fun called")
    email="ss@gmail.com"
    access_token = get_access_token(email)
    if not access_token:
        logging.error("Access token not found in session.")
        return redirect(HOME_PAGE_URL)  # Redirect to log in if access token is not available
    print("access_token: "+ access_token)
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    object_types = ['contacts', 'deals', 'companies']
    tables = []

    for object_type in object_types:
        url = f'https://api.hubapi.com/crm/v3/schemas/{object_type}'
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            # Append the table's name and label to the tables list
            tables.append({
                'name': object_type,
                'label': data.get('label', object_type.capitalize())  # Fallback to capitalized name if label isn't present
            })
        else:
            logging.error(f"Error fetching schema for {object_type}: {response.json()}")
            # You can choose to return an error response or continue populating tables list.
            # Consider appending error handling or default value if needed.

    return tables  # Return the list of tables

def fetch_hubspot_table_fields(table_name):
    """Fetch available fields for a specified HubSpot object type."""
    email = "ss@gmail.com"
    access_token = get_access_token(email=email)
    if not access_token:
        logging.error("Access token not found in session.")
        return []

    url = f"{HUBSPOT_API_URL}/crm/v3/properties/{table_name}"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    print("get fields url : "+url)
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        if response.status_code == 200:
            data = response.json()
            fields = [{'name': prop['name'], 'label': prop['label']} for prop in data['results']]
            # return json.dumps({'fields': fields})
            return jsonify({'fields': fields}), 200
        else:
            logging.error(f"Error fetching fields for {table_name}: {response.json()}")
            # return json.dumps({'fields': []})  # Return empty fields on error
            jsonify({'fields': []}), response.status_code
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching fields for {table_name}: {str(e)}")
        return jsonify({'error': 'Failed to fetch fields.', 'details': str(e)}), 500  # Return 500 on request errors

def hubspot_data_sync_to_sheet(email,hubspot_table_name,hubspot_selected_fields):

    access_token = get_access_token(email=email)
    if not access_token:
        return redirect(HOME_PAGE_URL)

    # HubSpot API headers
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    # Fetch records from the selected HubSpot object
    all_objects = []
    has_more = True
    after = None

    while has_more:
        url = f'https://api.hubapi.com/crm/v3/objects/{hubspot_table_name}'
        params = {
            'limit': 20,
            'properties': hubspot_selected_fields
        }
        if after:
            params['after'] = after

        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            return f"Error: {response.text}"

        data = response.json()
        all_objects.extend(data.get('results', []))
        has_more = data.get('paging', {}).get('next', {}).get('after') is not None
        after = data.get('paging', {}).get('next', {}).get('after')

    # Create a new Google Sheet
    new_sheet_id = create_google_sheet(f"HubSpot_{hubspot_table_name}")
    sheet_url = f"https://docs.google.com/spreadsheets/d/{new_sheet_id}/edit"
    share_google_sheet(new_sheet_id, email)
    # Store the fetched data into the Google Sheet
    store_in_google_sheets(all_objects, new_sheet_id, hubspot_table_name)


def batch_update_or_insert_objects(email,object_type, objects):
    url_base = f"https://api.hubapi.com/crm/v3/objects/{object_type}/"
    access_token = get_access_token(email=email)
    if not access_token:
        logging.error("Access token not found in session.")
        return []
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    # Prepare inputs for batch processing
    inputs = []
    for obj in objects:
        properties = obj.get('properties', {})
        object_id = obj.get('id')  # Assuming object ID is provided for updates
        if object_id:
            inputs.append({
                "id": object_id,
                "properties": properties
            })
        else:
            inputs.append({
                "properties": properties
            })

    # Determine whether to update or insert
    if any('id' in obj for obj in objects):
        # Batch update objects
        url = f"{url_base}batch"
        response = requests.patch(url, json={"inputs": inputs}, headers=headers)
    else:
        # Batch create objects
        url = f"{url_base}batch"
        response = requests.post(url, json={"inputs": inputs}, headers=headers)

    if response.status_code in (200, 202):
        return jsonify({"message": f"{object_type.capitalize()} processed successfully",
                        "data": response.json()}), response.status_code
    else:
        return jsonify({"error": f"Error processing {object_type}", "details": response.json()}), response.status_code















# un used method
def fetch_hubspot_objects(object_type, properties):
    """Fetch objects of a specified type from HubSpot."""
    access_token = get_access_token(email="")
    if not access_token:
        logging.error("Access token not found in session.")
        return None

    url = f"{HUBSPOT_API_URL}/crm/v3/objects/{object_type}"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    params = {
        'limit': 100,  # Change as necessary
        'properties': properties
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raises an error for HTTP error codes
        return response.json().get('results', [])
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching {object_type}: {str(e)}")
        return []