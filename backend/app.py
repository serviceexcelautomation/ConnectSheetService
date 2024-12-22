# app.py (main application file)
import os
from datetime import timedelta

from flask import Flask, session
from flask_cors import CORS

from backend.data_source import datasource_bp
from backend.registration_login import registration_login_bp
from backend.hubspot_integration import hubspot_bp
from flask_session import Session
import redis

# Create Flask application
app = Flask(__name__)

# Allow CORS for all domains; adjust as needed for production
CORS(app)

# Set the secret key for session management
app.secret_key = os.urandom(24)

# Configure Redis as the session interfaceS
#app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False  # Change to True if you want permanent sessions
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_KEY_PREFIX'] = 'myapp:'  # Prefix for session keys
#app.config['SESSION_REDIS'] = redis.StrictRedis(host='localhost', port=6379, db=0)  # Configure Redis connection
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)  # Adjust as needed

# Initialize the session
Session(app)

#Register data_source
app.register_blueprint(datasource_bp)
#Register user and login
app.register_blueprint(registration_login_bp)
# Register the HubSpot blueprint
app.register_blueprint(hubspot_bp)

if __name__ == '__main__':
    app.run( host="0.0.0.0",port=5000)
