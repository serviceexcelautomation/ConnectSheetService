from flask import jsonify
from psycopg2 import DatabaseError
import logging
from backend.common.postgres_db.postgres_conn import get_db_connection
# Logger configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def psql_conn():
    psql_connection= get_db_connection()
    return psql_connection
def authenticate_datasource_db(user_id, source_id, source_name, source_auth_token,status):
    try:
        conn = psql_conn()
        cursor = conn.cursor()

        query = """
               INSERT INTO datasource_auth (userid, sourceid, source_name, source_auth_token, created_at, status)
               VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, %s)
               RETURNING auth_id;
           """
        cursor.execute(query, (user_id, source_id, source_name, source_auth_token,status))
        auth_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        logger.info({"message": "Data source authentication successful", "auth_id": auth_id})
        return jsonify({"message": "Data source authentication successful", "auth_id": auth_id}), 201
    except (Exception, DatabaseError) as e:
        logger.error({"message": f"Error authenticating datasource: {e}", "user_id": user_id,"sourceid":source_id})
        return jsonify({"error": "Failed to authenticate with the data source"}), 500

def get_source_auth_token(user_id, source_id):
    try:
        conn = psql_conn()
        cursor = conn.cursor()

        query = """
            SELECT source_auth_token 
            FROM datasource_auth
            WHERE userid = %s AND sourceid = %s;
        """
        cursor.execute(query, (user_id, source_id))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result:
            source_auth_token = result[0]
            logger.info({"message": "Source auth token retrieved successfully", "user_id": user_id, "source_id": source_id})
            return jsonify({"message": "Source auth token retrieved successfully", "source_auth_token": source_auth_token}), 200
        else:
            logger.warning({"message": "Source auth token not found", "user_id": user_id, "source_id": source_id})
            return jsonify({"error": "Source auth token not found"}), 404
    except (Exception, DatabaseError) as e:
        logger.error({"message": f"Error authenticating datasource: {e}", "user_id": user_id, "sourceid": source_id})
        return jsonify({"error": "Failed to authenticate with the data source"}), 500
