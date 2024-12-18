# hubspot_integration/hubspot_routes.py
import os
from crypt import methods

from flask import request, jsonify, session, redirect
from dotenv import load_dotenv

from backend.common.access_token.redis_connection import RedisConnection
from .hubspot_postgres import authenticate_datasource_db

# Load environment variables
load_dotenv()

from . import hubspot_bp
from .hubspot_api_service import fetch_hubspot_objects, fetch_hubspot_table_fields, fetch_hubspot_tables, \
    hubspot_data_sync_to_sheet, batch_update_or_insert_objects
from .hubspot_auth import  generate_access_token

# Load environment variables for configuration
AUTHORIZATION_URL = os.getenv("HUBSPOT_AUTHORIZATION_URL")
CLIENT_ID = os.getenv("HUBSPOT_CLIENT_ID")
REDIRECT_URI = os.getenv("HUBSPOT_REDIRECT_URI")
SCOPES = os.getenv("SCOPES")
FRONT_END_OBJECT_SELECTION_URL=os.getenv("FRONT_END_OBJECT_SELECTION_URL")
# redis_connection = RedisConnection()

@hubspot_bp.route('/hubspot/auth/page',methods=['GET'])
def login():
    # Check if required environment variables are set

    if not AUTHORIZATION_URL or not CLIENT_ID or not REDIRECT_URI or not SCOPES:
        error_message = {
            "error": "Missing environment variables for HubSpot OAuth configuration."
        }
        return jsonify(error_message), 500  # Return 500 Internal Server Error

    # Construct the authorization URL
    auth_url = f"{AUTHORIZATION_URL}?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={SCOPES}"

    try:
        # Redirect to HubSpot authorization URL
        return {"auth_url":auth_url},200
    except Exception as e:
        error_message = {
            "error": "Failed to redirect to HubSpot authorization URL.",
            "details": str(e)  # Capture any exception details
        }
        return jsonify(error_message), 500  # Return 500 Internal Server Error

@hubspot_bp.route('/hubspot/auth/callback', methods=['POST'])
def hubspot_auth_callback():
    """Handle HubSpot OAuth callback and set access token."""
    code = request.args.get('code')
    if not code:
        return jsonify({"error": "No code provided."}), 400
    data = request.get_json()
    user_id = data.get('user_id')
    source_id = data.get('source_id')
    source_name = data.get('source_name')
    if not user_id or not source_id or not source_name:
        return jsonify({"error": "All fields are required"}), 400

    try:
        response = generate_access_token(code)

        if response.status_code != 200:
            authenticate_datasource_db(user_id, source_id, source_name, None, 'failed')
            return jsonify({"error": response.json().get('message', 'Failed to obtain access token')}), 400

        else:
           source_auth_token = response.json().get('access_token')
           session['access_token']=source_auth_token
           authenticate_datasource_db(user_id, source_id, source_name, source_auth_token, 'success')

        # print("access_token : "+source_auth_token)
        #
        # session.permanent = True  # Makes the session permanent (if configured)
        # redis_connection.hset('user_tokens', email, source_auth_token)
        #return jsonify({"message": "Authorization successful.","access_token":access_token}), 200
        return redirect(FRONT_END_OBJECT_SELECTION_URL)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@hubspot_bp.route('/hubspot/tables', methods=['GET'])
def get_hubspot_tables():
    print("hubspot table route called")
    """Fetch available HubSpot CRM object schemas (tables)."""
    table_names = fetch_hubspot_tables()
    # print(table_names)

    # Ensure table_names is a list before returning
    if isinstance(table_names, list):
        return jsonify({'tables': table_names}),200
    else:
        return jsonify({'error': 'Failed to fetch tables'}), 500  # Handle unexpected response


@hubspot_bp.route('/hubspot/fields', methods=['GET'])
def get_hubspot_fields():
    table_name = request.args.get('table_name')
    """Endpoint to fetch HubSpot fields for a specific query parameter (e.g., ?table_name=deals)."""
    fields = fetch_hubspot_table_fields(table_name=table_name)
    return fields

@hubspot_bp.route('/hubspot/syncto/sheet', methods=['POST'])
def sync_hubspot_data_to_sheet():
    """Fetch selected HubSpot object data and store it in a Google Sheet."""
    # Get the user input from JSON body
    data = request.json  # Parse JSON body
    hubspot_table = data.get('hubspot_table')
    selected_fields = data.get('selected_fields')  # The selected fields from JSON body

    if not selected_fields:
        return "Error: Please select at least one field.", 400

    response=hubspot_data_sync_to_sheet(email="",hubspot_table_name=hubspot_table,hubspot_selected_fields=selected_fields)
    return response

@hubspot_bp.route('/hubspot/twowaysync/<object_type>', methods=['POST'])
def sync_google_sheet_data_to_hubspot(object_type):
    objects = request.json.get('objects')

    if not objects:
        return jsonify({"error": "No objects provided"}), 400
    response=batch_update_or_insert_objects(email = "",object_type = object_type,objects = objects)

    return response

