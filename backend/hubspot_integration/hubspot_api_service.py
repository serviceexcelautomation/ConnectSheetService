# hubspot_integration/hubspot_api.py

import logging
import os

import requests
from dotenv import load_dotenv
from flask import redirect, jsonify

from backend.common.google_sheet.google_sheet_service import create_google_sheet, share_google_sheet, \
    store_in_google_sheets
from backend.hubspot_integration.hubspot_auth import validate_and_refresh_token
from backend.hubspot_integration.hubspot_postgres import get_source_auth_token, get_connect_user_to_source, \
    connect_user_to_source_db, update_status_to_connected

# Load environment variables
load_dotenv()

HUBSPOT_API_URL = os.getenv("HUBSPOT_API_URL")
HOME_PAGE_URL=os.getenv("HOME_PAGE_URL")

# redis_connection = RedisConnection()

def get_access_token(user_id,source_id):
    """Retrieve the access token from the session."""
    response_token,statuscode=get_source_auth_token(user_id, source_id)
    # Extract JSON data from the Response object
    response_data = response_token.get_json()  # This will return a dictionary

    # Extract the source_auth_token from the dictionary
    source_auth_token = response_data.get("source_auth_token")
    return response_data

def get_user_email():
    # Implement this function to get the user's email or ID from HubSpot using the access token
    return "user@example.com"

# To get hubspot tables
def fetch_hubspot_tables(user_id,source_id):
    tokens = get_access_token(user_id, source_id)
    access_token = tokens.get("source_auth_token")
    refresh_token = tokens.get("refresh_token")
    # Validate and refresh the token
    access_token = validate_and_refresh_token(user_id, source_id, access_token, refresh_token)

    if not access_token:
        logging.error("Access token not found in session.")
        return {"message":"Access token not found in session."}  # Redirect to log in if access token is not available

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    object_types = ['contacts', 'deals', 'companies']
    tables = []

    for object_type in object_types:
        url = f'https://api.hubapi.com/crm/v3/schemas/{object_type}'
        response = requests.get(url, headers=headers)
        if response.status_code == 401:  # Token expired
            logging.info("Access token expired. Refreshing token.")

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

def fetch_hubspot_table_fields(table_name,user_id,source_id):
    tokens = get_access_token(user_id, source_id)
    access_token = tokens.get("source_auth_token")
    refresh_token = tokens.get("refresh_token")
    # Validate and refresh the token
    access_token = validate_and_refresh_token(user_id, source_id,access_token,refresh_token)
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
            return jsonify({'table_name':table_name,'fields': fields}), 200
        else:
            logging.error(f"Error fetching fields for {table_name}: {response.json()}")
            # return json.dumps({'fields': []})  # Return empty fields on error
            jsonify({'table_name':table_name,'fields': []}), response.status_code
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching fields for {table_name}: {str(e)}")
        return jsonify({'error': 'Failed to fetch fields.', 'details': str(e)}), 500  # Return 500 on request errors

def hubspot_data_sync_to_sheet(user_id, source_id, sync_frequency, googlesheet_name, googlesheet_id, additional_emails, hubspot_table_name, hubspot_selected_fields):
    tokens = get_access_token(user_id, source_id)
    access_token = tokens.get("source_auth_token")
    refresh_token = tokens.get("refresh_token")

    # Validate and refresh the token
    access_token = validate_and_refresh_token(user_id, source_id, access_token, refresh_token)
    if not access_token:
        return redirect(HOME_PAGE_URL)

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    for table_name in hubspot_table_name:
        all_objects = []
        has_more = True
        after = None

        while has_more:
            url = f'https://api.hubapi.com/crm/v3/objects/{table_name}'
            params = {
                'limit': 20,
                'properties': hubspot_selected_fields
            }
            if after:
                params['after'] = after

            response = requests.get(url, headers=headers, params=params)
            if response.status_code != 200:
                return jsonify({"error": f"Error fetching data from HubSpot: {response.text}"}), 500

            data = response.json()
            all_objects.extend(data.get('results', []))
            has_more = data.get('paging', {}).get('next', {}).get('after') is not None
            after = data.get('paging', {}).get('next', {}).get('after')

        if not googlesheet_id:
            new_sheet_id = create_google_sheet(f"HubSpot_{googlesheet_name}")
            share_google_sheet(new_sheet_id, additional_emails)
            googlesheet_id = new_sheet_id

        sheet_url = f"https://docs.google.com/spreadsheets/d/{googlesheet_id}/edit"

        if all_objects:
            response = store_in_google_sheets(
                objects=all_objects,
                sheet_id=googlesheet_id,
                work_sheet_name=table_name,
                selected_fields=hubspot_selected_fields
            )
            connect_user_to_source_db(
                user_id=user_id,
                source_id=source_id,
                sync_frequency=sync_frequency,
                googlesheet_name=googlesheet_name,
                googlesheet_id=sheet_url,
                additional_emails=additional_emails,
                list_of_fieldnames=hubspot_selected_fields,
                list_of_table_names=hubspot_table_name
            )
            update_status_to_connected(user_id=user_id, source_id=source_id)  # Update status to 'connected'
            return response

    return jsonify({"message": "Data synchronization completed successfully."}), 200


def get_hubspot_data_sync_to_sheet_info(user_id,source_id):
    return get_connect_user_to_source(user_id=user_id,source_id=source_id)












def batch_update_or_insert_objects(user_id,source_id,email,object_type, objects):
    url_base = f"https://api.hubapi.com/crm/v3/objects/{object_type}/"
    access_token = get_access_token(user_id,source_id)
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