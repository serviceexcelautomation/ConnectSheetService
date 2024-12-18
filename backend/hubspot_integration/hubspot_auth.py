# hubspot_integration/hubspot_auth.py

import os
import requests
from flask import session, jsonify
from dotenv import load_dotenv

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

    response = requests.post(TOKEN_URL, data=token_data)
    return response
