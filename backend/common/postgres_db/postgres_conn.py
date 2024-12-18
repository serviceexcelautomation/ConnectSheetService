import random
import string

import psycopg2
import datetime
import uuid
import logging
from werkzeug.security import check_password_hash
from flask import jsonify, request

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

# Logger configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection settings
DB_HOST = '15.207.152.160'
DB_NAME = 'sheet_automation'
DB_USER = 'automation'
DB_PASSWORD = 'auto@2025'
DB_PORT = '5432'

# SMTP Configuration for Email (Update with your SMTP details)
SMTP_HOST = 'email-smtp.ap-south-1.amazonaws.com'  # Replace with your SMTP host
SMTP_PORT = 587  # Common SMTP port (for TLS)
SMTP_USER_NAME = 'AKIAQ5NPIYLILEC3UHON'
SMTP_PASSWORD = 'BJ/TScFfQZ8CZvykZQgIijKDHQCXcgpSPfs5jpjFQkRw'  # Replace with your SMTP password
SMTP_EMAIL='information@aastrika.org'  # Replace with your SMTP username


# Function to generate random OTP
def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))


# Function to send OTP email via SMTP
def send_otp_email(user_email: str, otp: str):
    try:

        # Set up the MIME message
        msg = MIMEMultipart()
        msg['From'] = SMTP_EMAIL
        msg['To'] = user_email
        msg['Subject'] = 'Your OTP Code'

        # Body of the email
        body = f"Your OTP code is {otp}. Please use it to verify your registration."
        msg.attach(MIMEText(body, 'plain'))

        # Connect to the SMTP server and send the email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()  # Secure the connection
            server.login(SMTP_USER_NAME, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, user_email, msg.as_string())
            logger.info(f"OTP sent to {user_email}")

    except Exception as e:
        logger.error(f"Failed to send OTP email: {str(e)}")
        raise


# Helper function to connect to the database
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise


# Refactor functions with context management

def user_registration_insert_db(username, email, password_hash):
    try:
        # Step 1: Check if the email already exists
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT user_id FROM user_registration WHERE email = %s", (email,)
                )
                existing_user = cur.fetchone()

                # If the email already exists, raise an error
                if existing_user:
                    return jsonify({"message": "Email already exists. Please use a different email address.","email":email}), 400

        # Step 2: If email does not exist, proceed with registration
        otp = generate_otp()
        otp_created_at = datetime.datetime.now()
        otp_expires_at = otp_created_at + datetime.timedelta(minutes=1)

        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Insert user registration data
                cur.execute(
                    "INSERT INTO user_registration (username, email, password_hash, otp, otp_created_at, otp_expires_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s) RETURNING user_id",
                    (username, email, password_hash, otp, otp_created_at, otp_expires_at)
                )
                user_id = cur.fetchone()[0]

                # Insert OTP verification data
                cur.execute(
                    "INSERT INTO otp_verifications (user_id, otp, expires_at) VALUES (%s, %s, %s)",
                    (user_id, otp, otp_expires_at)
                )
                conn.commit()

        # Send OTP email
        send_otp_email(email, otp)

        return jsonify({"message": "User registered successfully, OTP sent!", "user_id": user_id}), 201

    except Exception as e:
        logger.error(f"Error during user registration insert: {str(e)}")
        raise

def verify_otp_db(user_id, otp):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Retrieve OTP verification record
                cur.execute(
                    "SELECT otp, expires_at, status FROM otp_verifications WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
                    (user_id,)
                )
                otp_entry = cur.fetchone()

                if not otp_entry:
                    return jsonify({"error": "No OTP found for this user"}), 404

                db_otp, expires_at, status = otp_entry

                # Check OTP expiration
                if datetime.datetime.now() > expires_at:
                    return jsonify({"error": "OTP has expired"}), 400

                if status == 'used':
                    return jsonify({"error": "OTP has already been used"}), 400

                # Verify OTP
                if otp == db_otp:
                    cur.execute("UPDATE otp_verifications SET status = 'used' WHERE user_id = %s AND otp = %s", (user_id, otp))
                    conn.commit()

                    return jsonify({"message": "OTP verified successfully"}), 200
                else:
                    return jsonify({"error": "Invalid OTP"}), 400
    except Exception as e:
        logger.error(f"Error verifying OTP: {str(e)}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500


def otp_resend_db(user_id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT otp_verifications.otp, expires_at, status, email FROM otp_verifications "
                    "JOIN user_registration ON otp_verifications.user_id = user_registration.user_id "
                    "WHERE otp_verifications.user_id = %s ORDER BY otp_verifications.created_at DESC LIMIT 1",
                    (user_id,)
                )
                otp_entry = cur.fetchone()

                if not otp_entry:
                    return jsonify({"error": "No OTP found for this user"}), 404

                db_otp, expires_at, status, email = otp_entry

                if datetime.datetime.now() < expires_at:
                    return jsonify({"message": "OTP is still valid, no need to resend."}), 400

                # Generate a new OTP
                new_otp = generate_otp()
                new_otp_expires_at = datetime.datetime.now() + datetime.timedelta(minutes=5)

                cur.execute("UPDATE otp_verifications SET otp = %s, expires_at = %s, status = 'pending' WHERE user_id = %s", (new_otp, new_otp_expires_at, user_id))
                conn.commit()

                # Send the new OTP to the user
                send_otp_email(email, new_otp)

                return jsonify({"message": "New OTP sent successfully!"}), 200
    except Exception as e:
        logger.error(f"Error resending OTP: {str(e)}")
        return jsonify({"error": f"Database error: {str(e)}"}), 500

def user_login_db(email, password):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Retrieve the user record based on the email
                cur.execute("SELECT user_id, password_hash FROM user_registration WHERE email = %s", (email,))
                user = cur.fetchone()

                if user:
                    user_id, password_hash = user
                    print(password_hash)
                    print(password)

                    # Check if the provided password matches the stored password hash
                    if password_hash== password:
                        # Generate a new login ID using UUID
                        # login_id = str(uuid.uuid4())

                        # Get the user's IP address from the request context
                        ip_address = request.remote_addr  # Ensure you're inside a Flask route context

                        # Set the login status to "successful"
                        login_status = 'successful'
                        message = None  # No message for successful login

                        # Insert the login attempt record into the database
                        cur.execute(
                            """
                            INSERT INTO login_attempts (user_id, login_timestamp, login_status, ip_address, message)
                            VALUES ( %s, CURRENT_TIMESTAMP, %s, %s, %s)
                            """,
                            ( user_id, login_status, ip_address, message)
                        )
                        conn.commit()

                        # Return success response
                        return jsonify({"message": "Login successful", "login_id": user_id}), 200
                    else:
                        # Login failed: Incorrect password
                        login_status = 'failed'
                        message = 'Invalid credentials'
                        # Get the user's IP address from the request context
                        ip_address = request.remote_addr

                        # Insert the failed login attempt record
                        # login_id = str(uuid.uuid4())
                        cur.execute(
                            """
                            INSERT INTO login_attempts (user_id, login_timestamp, login_status, ip_address, message)
                            VALUES (%s, CURRENT_TIMESTAMP, %s, %s, %s)
                            """,
                            (user_id, login_status, ip_address, message)
                        )
                        conn.commit()

                        # Return error response for failed login
                        return jsonify({"message": message, "login_id": user_id}), 401
                        # return jsonify({"error": message}), 401
                else:
                    # User not found
                    login_status = 'failed'
                    message = 'User not found'
                    # Get the user's IP address from the request context
                    ip_address = request.remote_addr

                    # Insert the failed login attempt record
                    # login_id = str(uuid.uuid4())
                    cur.execute(
                        """
                        INSERT INTO login_attempts (user_id, login_timestamp, login_status, ip_address, message)
                        VALUES ( %s, CURRENT_TIMESTAMP, %s, %s, %s)
                        """,
                        (None, login_status, ip_address, message)  # No user_id for non-existent user
                    )
                    conn.commit()

                    # Return error response if user not found
                    return jsonify({"message": message, "login_id": None}), 401
                    # return jsonify({"error": message}), 404

    except Exception as e:
        # Log the error and return a 500 error response
        logger.error(f"Error during user login: {str(e)}")
        return jsonify({"message": f"Database error: {str(e)}"}), 500

