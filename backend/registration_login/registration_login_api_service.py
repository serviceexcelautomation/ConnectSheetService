import hashlib
import uuid
import datetime
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from werkzeug.security import generate_password_hash, check_password_hash

from backend.common.postgres_db.postgres_conn import user_registration_insert_db, verify_otp_db, otp_resend_db, \
    user_login_db, get_user_info

# Logger configuration for production
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SMTP Configuration for Email (Update with your SMTP details)
SMTP_HOST = 'smtp.example.com'   # Replace with your SMTP host
SMTP_PORT = 587                  # Common SMTP port (for TLS)
SMTP_USER = 'your_email@example.com'  # Replace with your SMTP username
SMTP_PASSWORD = 'your_password'       # Replace with your SMTP password

#
# # Function to generate random OTP
# def generate_otp(length=6):
#     return ''.join(random.choices(string.digits, k=length))
#
#
# # Function to send OTP email via SMTP
# def send_otp_email(user_email: str, otp: str):
#     try:
#         # Set up the MIME message
#         msg = MIMEMultipart()
#         msg['From'] = SMTP_USER
#         msg['To'] = user_email
#         msg['Subject'] = 'Your OTP Code'
#
#         # Body of the email
#         body = f"Your OTP code is {otp}. Please use it to verify your registration."
#         msg.attach(MIMEText(body, 'plain'))
#
#         # Connect to the SMTP server and send email
#         with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
#             server.starttls()  # Secure the connection
#             server.login(SMTP_USER, SMTP_PASSWORD)
#             server.sendmail(SMTP_USER, user_email, msg.as_string())
#             logger.info(f"OTP sent to {user_email}")
#
#     except Exception as e:
#         logger.error(f"Failed to send OTP email: {str(e)}")
#         raise


def user_registration_insert(username, email, password_hash):
    userid=user_registration_insert_db(username, email, password_hash)
    return userid
def read_user_registration(user_id,email):
    user_response=get_user_info(user_id,email)
    return user_response

def verify_otp_get(user_id,otp):
    response_msg=verify_otp_db(user_id,otp)
    return response_msg

def resend_otp_post(user_id):
    return_msg=otp_resend_db(user_id)
    return return_msg

def user_login(email,password):
     return user_login_db(email,password)



