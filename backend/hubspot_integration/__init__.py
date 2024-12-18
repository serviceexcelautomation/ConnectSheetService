# hubspot_integration/__init__.py

from flask import Blueprint

hubspot_bp = Blueprint('hubspot', __name__)

from . import hubspot_routes

