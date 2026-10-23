"""Showcase routes: submit, list, view completed project showcases — SQLite."""
import json

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from database import get_db
from models import Showcase, User, UserProject
from utils.helpers import generate_id, now_iso, sanitize_string

showcase_bp = Blueprint('showcase', __name__)


# ── Serialiser ─────────────────────────────────────────────────────────────────

def _showcase_to_dict(s):
    return s.to_dict()


# ── Routes ─────────────────────────────────────────────────────────────────────

@showcase_bp.route('', methods=['GET'])
def list_showcases():
    """List all project showcases, newest first."""
    with get_db() as db:
        showcases = (
            db.query(Showcase)
            .order_by(Showcase.created_at.desc())
            .all()
        )
        result = [_showcase_to_dict(s) for s in showcases]
    return jsonify({'showcases': result}), 200


@showcase_bp.route('', methods=['POST'])
@jwt_required()
def submit_showcase():
    """Submit a completed project to the showcase."""
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    project_id = data.get('projectId', '')

    with get_db() as db:
        user = db.get(User, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Verify project is completed
        completed = (
            db.query(UserProject)
            .filter(
                UserProject.user_id == user_id,
                UserProject.project_id == project_id,
                UserProject.status == 'completed',
            )
            .first()
        )
        if not completed:
            return jsonify({'error': 'You can only showcase completed projects'}), 403

        technologies = data.get('technologies', [])
        if isinstance(technologies, list):
            technologies = json.dumps(technologies, ensure_ascii=False)

        showcase = Showcase(
            id=generate_id(),
            user_id=user_id,
            user_name=user.name,
            project_id=project_id,
            project_name=sanitize_string(data.get('projectName', '')),
            description=sanitize_string(data.get('description', '')),
            technologies=technologies,
            screenshot_url=sanitize_string(data.get('screenshotUrl', '')),
            demo_url=sanitize_string(data.get('demoUrl', '')),
            github_url=sanitize_string(data.get('githubUrl', '')),
            what_i_learned=sanitize_string(data.get('whatILearned', '')),
            challenges_faced=sanitize_string(data.get('challengesFaced', '')),
            created_at=now_iso(),
        )
        db.add(showcase)
        db.flush()
        result = _showcase_to_dict(showcase)

    return jsonify({'message': 'Showcase submitted', 'showcase': result}), 201


@showcase_bp.route('/user/<target_user_id>', methods=['GET'])
def user_showcases(target_user_id):
    """Get showcases for a specific user."""
    with get_db() as db:
        showcases = (
            db.query(Showcase)
            .filter(Showcase.user_id == target_user_id)
            .order_by(Showcase.created_at.desc())
            .all()
        )
        result = [_showcase_to_dict(s) for s in showcases]
    return jsonify({'showcases': result}), 200
