# hubspot_integration/hubspot_auth.py

import os
import requests
from flask import session, jsonify
from dotenv import load_dotenv
import logging
from backend.hubspot_integration.hubspot_postgres import update_access_token
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Load environment variables
load_dotenv()

HUBSPOT_CLIENT_ID = os.getenv("HUBSPOT_CLIENT_ID")
HUBSPOT_CLIENT_SECRET = os.getenv("HUBSPOT_CLIENT_SECRET")
HUBSPOT_REDIRECT_URI = os.getenv("HUBSPOT_REDIRECT_URI")
TOKEN_URL = os.getenv("HUBSPOT_TOKEN_URL")

def generate_access_token(code):
    """Exchange the authorization code for an access token."""
    token_data = {
        'grant_type': 'authorization_code',
        'client_id': HUBSPOT_CLIENT_ID,
        'client_secret': HUBSPOT_CLIENT_SECRET,
        'redirect_uri': HUBSPOT_REDIRECT_URI,
        'code': code
    }
    print(token_data)
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.post(TOKEN_URL, data=token_data, headers=headers)
    print(response.status_code)
    print(response.json())
    return response

def refresh_access_token(refresh_token):
    """Refresh the access token using the refresh token."""
    global new_access_token
    try:
        token_data = {
            'grant_type': 'refresh_token',
            'client_id': HUBSPOT_CLIENT_ID,
            'client_secret': HUBSPOT_CLIENT_SECRET,
            'refresh_token': refresh_token
        }
        refresh_response = requests.post(TOKEN_URL, data=token_data)
        refresh_response.raise_for_status()
        # if refresh_response.status_code == 200:
            # tokens = refresh_response.json()
            # new_access_token = tokens.get('access_token')
            # new_refresh_token = tokens.get('refresh_token', refresh_token)  # Fallback to the old refresh token
            #
            # # Update tokens in database
            # update_access_token(user_id, source_id, new_access_token, new_refresh_token)
            # # logging.info("Access token refreshed and updated in database.")

        return refresh_response
    except requests.RequestException as e:
        # logger.exception("Error refreshing access token.")
        raise e


def validate_and_refresh_token(user_id, source_id,access_token,refresh_token):
    """
    Validate the token and refresh it if expired.
    Returns a valid access token or raises an exception if unable to refresh.
    """
    try:
        # # Fetch tokens from the database
        # # tokens = get_access_token(user_id, source_id)
        # tokens=""
        # access_token = tokens.get("source_auth_token")
        # refresh_token = tokens.get("refresh_token")

        if not access_token:
            raise ValueError("Access token not found.")

        # Validate the token by making a lightweight API call
        headers = {'Authorization': f'Bearer {access_token}'}
        validation_url = f'https://api.hubapi.com/crm/v3/objects/contacts'

        response = requests.get(validation_url, headers=headers)

        if response.status_code == 200:
            # Token is valid
            logging.info("Access token not expired.")
            return access_token

        elif response.status_code == 401:  # Token expired
            logging.info("Access token expired. Attempting to refresh.")
            refresh_response = refresh_access_token(refresh_token)

            if refresh_response.status_code == 200:
                # Update the new tokens in the database
                tokens = refresh_response.json()
                new_access_token1 = tokens.get('access_token')
                new_refresh_token = tokens.get('refresh_token', refresh_token)
                update_access_token(user_id, source_id, new_access_token1, new_refresh_token)
                return new_access_token1
            else:
                raise ValueError("Failed to refresh access token. Please reauthenticate.")

        else:
            # Handle unexpected errors
            response.raise_for_status()

    except Exception as e:
        # logging.exception("Error validating or refreshing token.")
        raise e
