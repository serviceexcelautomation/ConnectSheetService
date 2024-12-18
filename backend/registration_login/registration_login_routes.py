from flask import request, jsonify
from backend.registration_login import registration_login_bp
from backend.registration_login.registration_login_api_service import user_registration_insert, verify_otp_get, \
    user_login, resend_otp_post


# Route: Register User (Create new user)
@registration_login_bp.route('/register', methods=['POST'])
def register_user():
    data = request.get_json()

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"error": "Missing required fields: username, email, or password"}), 400

    if '@' not in email or '.' not in email.split('@')[-1]:
        return jsonify({"error": "Invalid email format"}), 400

    # password_hash = hash_password(password)
    password_hash= password
    return user_registration_insert(username, email, password_hash)


# Route: OTP Verification (Verify OTP for the user)
@registration_login_bp.route('/verify_otp', methods=['POST'])
def verify_otp():
    data = request.get_json()

    user_id = data.get('user_id')
    otp = data.get('otp')

    if not user_id or not otp:
        return jsonify({"error": "Missing user_id or OTP"}), 400

    return verify_otp_get(user_id, otp)


# Route: Resend OTP (Resend OTP if expired)
@registration_login_bp.route('/resend_otp', methods=['POST'])
def resend_otp():
    data = request.get_json()

    user_id = data.get('user_id')
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    return resend_otp_post(user_id)


# Route: Login User (Authenticate and log user in)
@registration_login_bp.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400

    return user_login(email,password)