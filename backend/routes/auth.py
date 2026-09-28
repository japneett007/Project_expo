"""Authentication routes: register, login, logout, profile."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, set_access_cookies, unset_jwt_cookies,
    jwt_required, get_jwt_identity
)
import bcrypt
from utils.helpers import read_json, write_json, generate_id, now_iso, sanitize_string, validate_email
from middleware.rate_limit import rate_limit

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
@rate_limit('auth')
def register():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    name = sanitize_string(data.get('name', ''))
    email = sanitize_string(data.get('email', '')).lower()
    password = data.get('password', '')
    confirm_password = data.get('confirmPassword', '')

    # Validation
    if not name or len(name) < 2:
        return jsonify({'error': 'Name must be at least 2 characters'}), 400
    if not validate_email(email):
        return jsonify({'error': 'Invalid email format'}), 400
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    if password != confirm_password:
        return jsonify({'error': 'Passwords do not match'}), 400

    users = read_json('users.json')

    # Check existing
    if any(u['email'] == email for u in users):
        return jsonify({'error': 'Email already registered'}), 409

    # Hash password with bcrypt
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    user = {
        'id': generate_id(),
        'name': name,
        'email': email,
        'password': hashed,
        'profileImage': '',
        'degree': '',
        'branch': '',
        'semester': '',
        'skillLevel': 'beginner',
        'interestedDomains': [],
        'goals': [],
        'completedProjects': [],
        'currentProjects': [],
        'xp': 0,
        'achievements': [],
        'onboardingComplete': False,
        'activeDays': [],
        'copilotUsed': False,
        'createdAt': now_iso(),
        'updatedAt': now_iso()
    }

    users.append(user)
    write_json('users.json', users)

    # Create JWT token
    token = create_access_token(identity=user['id'])
    resp = jsonify({
        'message': 'Registration successful',
        'user': _safe_user(user)
    })
    set_access_cookies(resp, token)
    return resp, 201


@auth_bp.route('/login', methods=['POST'])
@rate_limit('auth')
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    email = sanitize_string(data.get('email', '')).lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    users = read_json('users.json')
    user = next((u for u in users if u['email'] == email), None)

    if not user:
        return jsonify({'error': 'Invalid email or password'}), 401

    if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        return jsonify({'error': 'Invalid email or password'}), 401

    token = create_access_token(identity=user['id'])
    resp = jsonify({
        'message': 'Login successful',
        'user': _safe_user(user)
    })
    set_access_cookies(resp, token)
    return resp, 200


@auth_bp.route('/logout', methods=['POST'])
def logout():
    resp = jsonify({'message': 'Logout successful'})
    unset_jwt_cookies(resp)
    return resp, 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    user_id = get_jwt_identity()
    users = read_json('users.json')
    user = next((u for u in users if u['id'] == user_id), None)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify({'user': _safe_user(user)}), 200


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    users = read_json('users.json')
    user_idx = next((i for i, u in enumerate(users) if u['id'] == user_id), None)
    if user_idx is None:
        return jsonify({'error': 'User not found'}), 404

    user = users[user_idx]

    # Whitelist allowed fields (prevent mass assignment)
    allowed_fields = [
        'name', 'profileImage', 'degree', 'branch', 'semester',
        'skillLevel', 'interestedDomains', 'goals', 'onboardingComplete'
    ]
    for field in allowed_fields:
        if field in data:
            if isinstance(data[field], str):
                user[field] = sanitize_string(data[field])
            else:
                user[field] = data[field]

    user['updatedAt'] = now_iso()
    users[user_idx] = user
    write_json('users.json', users)

    return jsonify({'message': 'Profile updated', 'user': _safe_user(user)}), 200


def _safe_user(user):
    """Return user dict without sensitive fields."""
    safe = {k: v for k, v in user.items() if k != 'password'}
    return safe
