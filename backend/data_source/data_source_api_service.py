from flask import jsonify
import logging
from backend.common.postgres_db.postgres_conn import get_db_connection
from datetime import datetime
from psycopg2 import sql, DatabaseError
# Logger configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def psql_conn():
    psql_connection= get_db_connection()
    return psql_connection

def data_source_db(sourcename, status):
    try:
        conn = psql_conn()
        cursor = conn.cursor()
        query = """
            INSERT INTO datasource (sourcename, status, created_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            RETURNING sourceid;
        """
        cursor.execute(query, (sourcename, status))
        sourceid = cursor.fetchone()[0]
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"message": "Datasource added successfully", "sourceid": sourceid}), 201
    except (Exception, DatabaseError) as e:
        logger.error(f"Error adding datasource: {e}")
        return jsonify({"message": "Failed to add datasource"}), 500


def get_all_data_source_db():
    try:
        conn = psql_conn()  # Assuming psql_conn is a function that returns a DB connection
        cursor = conn.cursor()

        query = "SELECT sourceid, sourcename, status, created_at FROM datasource"
        cursor.execute(query)

        # Fetch all rows from the database
        all_data_sources = cursor.fetchall()

        # Format the result as a list of dictionaries
        formatted_data_sources = []
        for row in all_data_sources:
            formatted_data_sources.append({
                "sourceid": row[0],
                "sourcename": row[1],
                "status": row[2],
                "created_at": row[3].strftime('%Y-%m-%d %H:%M:%S')  # Format timestamp to string
            })

        # Commit and close connections
        conn.commit()
        cursor.close()
        conn.close()

        # Return the result in the desired format
        return jsonify({"message": "success", "datasources": formatted_data_sources}), 200
    except (Exception, DatabaseError) as e:
        logger.error(f"Error fetching datasources: {e}")
        return jsonify({"message": "Failed to fetch datasources"}), 500