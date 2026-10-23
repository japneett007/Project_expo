"""Authentication routes: register, login, logout, me, profile — SQLite."""
import json

import bcrypt
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, set_access_cookies, unset_jwt_cookies,
    jwt_required, get_jwt_identity,
)

from database import get_db
from middleware.rate_limit import rate_limit
from models import User, UserProject, UserProjectMilestone, UserAchievement
from utils.helpers import generate_id, now_iso, sanitize_string, validate_email

auth_bp = Blueprint('auth', __name__)


# ── User serialiser ────────────────────────────────────────────────────────────

def _parse(value, default=None):
    if default is None:
        default = []
    if value is None:
        return default
    if isinstance(value, list):
        return value
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return default


def _safe_user(user: User, db) -> dict:
    """
    Return the user dict the frontend expects.

    Reconstructed fields (stored across multiple tables):
      - completedProjects: list of project_ids with status='completed'
      - currentProjects:   list of {projectId, startedAt, progress, milestones{}, completedMilestones[]}
      - achievements:      list of achievement_ids
    """
    # completedProjects
    completed_projects = [
        row.project_id
        for row in db.query(UserProject)
        .filter(UserProject.user_id == user.id, UserProject.status == 'completed')
        .order_by(UserProject.started_at)
        .all()
    ]

    # currentProjects
    active_ups = (
        db.query(UserProject)
        .filter(UserProject.user_id == user.id, UserProject.status == 'active')
        .all()
    )
    current_projects = []
    for up in active_ups:
        ms_rows = (
            db.query(UserProjectMilestone)
            .filter(
                UserProjectMilestone.user_id == user.id,
                UserProjectMilestone.project_id == up.project_id,
            )
            .all()
        )
        milestones_dict = {row.milestone_id: row.status for row in ms_rows}
        completed_ms = [mid for mid, status in milestones_dict.items() if status == 'completed']
        current_projects.append({
            'projectId': up.project_id,
            'startedAt': up.started_at,
            'progress': up.progress or 0,
            'milestones': milestones_dict,
            'completedMilestones': completed_ms,
        })

    # achievements
    achievements = [
        row.achievement_id
        for row in db.query(UserAchievement)
        .filter(UserAchievement.user_id == user.id)
        .all()
    ]

    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'profileImage': user.profile_image or '',
        'degree': user.degree or '',
        'branch': user.branch_id or '',           # frontend uses 'branch'
        'semester': user.semester or '',
        'skillLevel': user.skill_level or 'beginner',
        'interestedDomains': _parse(user.interested_domains),
        'goals': _parse(user.goals),
        'completedProjects': completed_projects,
        'currentProjects': current_projects,
        'xp': user.xp or 0,
        'achievements': achievements,
        'onboardingComplete': bool(user.onboarding_complete),
        'activeDays': _parse(user.active_days),
        'copilotUsed': bool(user.copilot_used),
        'createdAt': user.created_at,
        'updatedAt': user.updated_at,
    }


# ── Routes ─────────────────────────────────────────────────────────────────────

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

    if not name or len(name) < 2:
        return jsonify({'error': 'Name must be at least 2 characters'}), 400
    if not validate_email(email):
        return jsonify({'error': 'Invalid email format'}), 400
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    if password != confirm_password:
        return jsonify({'error': 'Passwords do not match'}), 400

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    now = now_iso()

    with get_db() as db:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            return jsonify({'error': 'Email already registered'}), 409

        user = User(
            id=generate_id(),
            name=name,
            email=email,
            password_hash=hashed,
            profile_image='',
            degree='',
            branch_id=None,   # FK to branches.id — NULL until user sets it
            semester='',
            skill_level='beginner',
            interested_domains='[]',
            goals='[]',
            xp=0,
            onboarding_complete=0,
            active_days='[]',
            copilot_used=0,
            created_at=now,
            updated_at=now,
        )
        db.add(user)
        db.flush()
        safe = _safe_user(user, db)
        uid = user.id

    token = create_access_token(identity=uid)
    resp = jsonify({'message': 'Registration successful', 'user': safe})
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

    with get_db() as db:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return jsonify({'error': 'Invalid email or password'}), 401
        if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return jsonify({'error': 'Invalid email or password'}), 401

        safe = _safe_user(user, db)
        uid = user.id

    token = create_access_token(identity=uid)
    resp = jsonify({'message': 'Login successful', 'user': safe})
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
    with get_db() as db:
        user = db.get(User, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        safe = _safe_user(user, db)
    return jsonify({'user': safe}), 200


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    with get_db() as db:
        user = db.get(User, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Whitelist — match old field names the frontend sends
        field_map = {
            'name': ('name', str),
            'profileImage': ('profile_image', str),
            'degree': ('degree', str),
            'branch': ('branch_id', str),          # frontend sends 'branch'
            'semester': ('semester', str),
            'skillLevel': ('skill_level', str),
            'interestedDomains': ('interested_domains', list),
            'goals': ('goals', list),
            'onboardingComplete': ('onboarding_complete', bool),
        }
        for frontend_key, (db_col, expected_type) in field_map.items():
            if frontend_key in data:
                val = data[frontend_key]
                if expected_type == str:
                    val = sanitize_string(val) if isinstance(val, str) else val
                    # branch_id is a FK — treat empty string as NULL
                    if db_col == 'branch_id' and val == '':
                        val = None
                elif expected_type == list:
                    val = json.dumps(val, ensure_ascii=False) if isinstance(val, list) else val
                elif expected_type == bool:
                    val = int(bool(val))
                setattr(user, db_col, val)

        user.updated_at = now_iso()
        db.flush()
        safe = _safe_user(user, db)

    return jsonify({'message': 'Profile updated', 'user': safe}), 200
