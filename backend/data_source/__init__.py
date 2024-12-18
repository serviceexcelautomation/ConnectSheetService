from flask import Blueprint

datasource_bp = Blueprint('datasource', __name__)

from . import data_source_api_routes