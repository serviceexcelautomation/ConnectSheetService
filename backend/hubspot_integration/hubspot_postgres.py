import datetime

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
def authenticate_datasource_db(user_id, source_id, source_name, source_auth_token,refresh_token,status):
    try:
        conn = psql_conn()
        cursor = conn.cursor()

        query = """
               INSERT INTO datasource_auth (userid, sourceid, source_name, source_auth_token,refresh_token, created_at, status)
               VALUES (%s, %s, %s, %s,%s, CURRENT_TIMESTAMP, %s)
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

def update_access_token(user_id, source_id, new_access_token, new_refresh_token):
    """
    Update access and refresh tokens in the datasource_auth table.
    """
    try:
        conn = psql_conn()  # Ensure you have a function that establishes a PostgreSQL connection
        cursor = conn.cursor()

        query = """
            UPDATE datasource_auth
            SET source_auth_token = %s,
                refresh_token = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE userid = %s AND sourceid = %s;
        """

        cursor.execute(query, (new_access_token, new_refresh_token, user_id, source_id))
        conn.commit()
        updated_rows = cursor.rowcount

        cursor.close()
        conn.close()

        if updated_rows > 0:
            logger.info({"message": "Tokens updated successfully", "user_id": user_id, "source_id": source_id})
            return {"message": "Tokens updated successfully"}
        else:
            logger.warning({"message": "No matching records found to update", "user_id": user_id, "source_id": source_id})
            return {"message": "No matching records found to update"}

    except (Exception, DatabaseError) as e:
        logger.error({"message": f"Error updating tokens: {e}", "user_id": user_id, "source_id": source_id})
        return {"error": "Failed to update tokens"}

def get_source_auth_token(user_id, source_id):
    try:
        conn = psql_conn()
        cursor = conn.cursor()

        query = """
            SELECT source_auth_token,refresh_token
            FROM datasource_auth
            WHERE userid = %s AND sourceid = %s;
        """
        cursor.execute(query, (user_id, source_id))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result:
            source_auth_token = result[0]
            refresh_token = result[1]
            print(source_auth_token)
            logger.info({"message": "Source auth token retrieved successfully", "user_id": user_id, "source_id": source_id})
            return jsonify({"message": "Source auth token retrieved successfully", "source_auth_token": source_auth_token,"refresh_token":refresh_token}), 200
        else:
            logger.warning({"message": "Source auth token not found", "user_id": user_id, "source_id": source_id})
            return jsonify({"error": "Source auth token not found"}), 404
    except (Exception, DatabaseError) as e:
        logger.error({"message": f"Error authenticating datasource: {e}", "user_id": user_id, "sourceid": source_id})
        return jsonify({"error": "Failed to authenticate with the data source"}), 500

def connect_user_to_source_db(user_id, source_id, sync_frequency, googlesheet_name, googlesheet_id, additional_emails, list_of_fieldnames, list_of_table_names):
    if not user_id or not source_id:
        return jsonify({"error": "user_id and source_id are required"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            INSERT INTO user_connected_datasource (
                userid, sourceid, status, sync_frequency, created_at,
                googlesheet_name, googlesheet_id, additional_emails,
                list_of_fieldnames, list_of_table_names
            )
            VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, %s, %s, %s, %s, %s)
            RETURNING user_connected_source_id;
        """
        cursor.execute(query, (
            user_id,
            source_id,
            'inprogress',
            sync_frequency,
            googlesheet_name,
            googlesheet_id,
            additional_emails,
            list_of_fieldnames,
            list_of_table_names
        ))
        user_connected_source_id = cursor.fetchone()[0]
        conn.commit()

        cursor.close()
        conn.close()
        logger.info(f"Successfully User connected to data source for user_id: {user_id}, source_id: {source_id}")
        return jsonify({
            "message": "User connected to data source",
            "user_connected_source_id": user_connected_source_id
        }), 201

    except (Exception, DatabaseError) as e:
        logger.error(f"Error connecting user to data source: {e}")
        return jsonify({"error": "Failed to connect user to data source"}), 500

def update_status_to_connected(user_id, source_id):
    """Update the status of the connection to 'connected'."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            UPDATE user_connected_datasource
            SET status = %s,last_sync=CURRENT_TIMESTAMP
            WHERE userid = %s AND sourceid = %s AND status = %s;
        """
        cursor.execute(query, ('connected', user_id, source_id, 'inprogress'))
        conn.commit()

        cursor.close()
        conn.close()
        logger.info(f"Successfully updated status to 'connected' for user_id: {user_id}, source_id: {source_id}")
    except (Exception, DatabaseError) as e:
        logger.error(f"Error updating status to 'connected': {e}")
        raise

def get_connect_user_to_source(user_id, source_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT * FROM user_connected_datasource 
            WHERE userid = %s AND sourceid = %s;
        """
        cursor.execute(query, (user_id, source_id))
        columns = [desc[0] for desc in cursor.description]  # Get column names
        data = cursor.fetchall()

        cursor.close()
        conn.close()

        if not data:
            return jsonify({"message": "No data found for the given userid and sourceid"}), 404

        # Map each row to a dictionary with column names
        result = [dict(zip(columns, row)) for row in data]

        return jsonify({"data": result}), 200
    except (Exception, DatabaseError) as e:
        print(f"Error retrieving data: {e}")
        return jsonify({"error": "Failed to retrieve data"}), 500

