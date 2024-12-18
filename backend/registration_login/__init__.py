from flask import Blueprint

registration_login_bp = Blueprint('registration_login', __name__)

from . import registration_login_routes
