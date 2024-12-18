import datetime

from dotenv import load_dotenv
from flask import request, jsonify
from psycopg2 import DatabaseError

from backend.common.postgres_db.postgres_conn import get_db_connection
from backend.data_source import datasource_bp
from backend.data_source.data_source_api_service import get_all_data_source_db, data_source_db

# Load environment variables
load_dotenv()

@datasource_bp.route('/datasource', methods=['POST'])
def add_datasource():
    data = request.get_json()
    sourcename = data.get('sourcename')
    status = data.get('status')

    if not sourcename:
        return jsonify({"error": "sourcename is required"}), 400

    return data_source_db(sourcename,status)

@datasource_bp.route('/datasource', methods=['GET'])
def list_data_sources():
    return get_all_data_source_db()

#  #2. **POST /datasource/auth** - Authenticate user with data source and store credentials.
# @datasource_bp.route('/datasource/auth', methods=['POST'])
# def authenticate_datasource():
#     data = request.get_json()
#     user_id = data.get('user_id')
#     source_id = data.get('source_id')
#     source_name = data.get('source_name')
#     # source_auth_token = data.get('source_auth_token')
#
#     if not user_id or not source_id or not source_name:
#         return jsonify({"error": "All fields are required"}), 400
#
#     # Get the code from the URL parameters (OAuth code)
#     code = request.args.get('code')
#     if not code:
#         return jsonify({"error": "No code provided."}), 400
#
#
#     try:
#         conn = get_db_connection()
#         cursor = conn.cursor()
#
#         query = """
#             INSERT INTO datasource_auth (userid, sourceid, source_name, source_auth_token, created_at, status)
#             VALUES (%s, %s, %s, %s, %s, %s)
#             RETURNING auth_id;
#         """
#         cursor.execute(query, (user_id, source_id, source_name, source_auth_token, datetime.utcnow(), 'success'))
#         auth_id = cursor.fetchone()[0]
#         conn.commit()
#
#         cursor.close()
#         conn.close()
#
#         return jsonify({"message": "Data source authentication successful", "auth_id": auth_id}), 201
#     except (Exception, DatabaseError) as e:
#         logger.error(f"Error authenticating datasource: {e}")
#         return jsonify({"error": "Failed to authenticate with the data source"}), 500



# 3. **POST /user/connect** - Connect user to a data source.
@datasource_bp.route('/user/connect', methods=['POST'])
def connect_user_to_source():
    data = request.get_json()
    user_id = data.get('user_id')
    source_id = data.get('source_id')
    sync_frequency = data.get('sync_frequency', '1day')
    googlesheet_name = data.get('googlesheet_name', '')
    googlesheet_id = data.get('googlesheet_id', '')
    list_of_fieldnames = data.get('list_of_fieldnames', [])
    list_of_table_names = data.get('list_of_table_names', [])

    if not user_id or not source_id:
        return jsonify({"error": "user_id and source_id are required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            INSERT INTO user_connected_source (userid, sourceid, status, sync_frequency, created_at, 
                                                googlesheet_name, googlesheet_id, list_of_fieldnames, list_of_table_names)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING user_connected_source_id;
        """
        cursor.execute(query, (
            user_id, source_id, 'inprogress', sync_frequency, datetime.utcnow(),
            googlesheet_name, googlesheet_id, list_of_fieldnames, list_of_table_names
        ))
        user_connected_source_id = cursor.fetchone()[0]
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"message": "User connected to data source", "user_connected_source_id": user_connected_source_id}), 201
    except (Exception, DatabaseError) as e:
        # logger.error(f"Error connecting user to data source: {e}")
        return jsonify({"error": "Failed to connect user to data source"}), 500



# 5. **GET /user/connected_sources** - List all data sources connected to a specific user.
@datasource_bp.route('/user/connected_sources', methods=['GET'])
def list_user_connected_sources():
    user_id = request.args.get('user_id')

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT ucs.user_connected_source_id, ucs.sourceid, ucs.status, ucs.sync_frequency, ucs.googlesheet_name,
                   ucs.googlesheet_id, ucs.list_of_fieldnames, ucs.list_of_table_names
            FROM user_connected_source ucs
            WHERE ucs.userid = %s;
        """
        cursor.execute(query, (user_id,))
        connected_sources = cursor.fetchall()
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"connected_sources": connected_sources}), 200
    except (Exception, DatabaseError) as e:
        # logger.error(f"Error fetching connected sources: {e}")
        return jsonify({"error": "Failed to fetch user connected sources"}), 500
