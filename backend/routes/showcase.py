"""Showcase routes: submit, list, view completed project showcases."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.helpers import read_json, write_json, generate_id, now_iso, sanitize_string

showcase_bp = Blueprint('showcase', __name__)


@showcase_bp.route('', methods=['GET'])
def list_showcases():
    """List all project showcases."""
    showcases = read_json('showcases.json')
    showcases.sort(key=lambda s: s.get('createdAt', ''), reverse=True)
    return jsonify({'showcases': showcases}), 200


@showcase_bp.route('', methods=['POST'])
@jwt_required()
def submit_showcase():
    """Submit a completed project to the showcase."""
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    users = read_json('users.json')
    user = next((u for u in users if u['id'] == user_id), None)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    project_id = data.get('projectId', '')
    # Verify project is completed
    if project_id not in user.get('completedProjects', []):
        return jsonify({'error': 'You can only showcase completed projects'}), 403

    showcase = {
        'id': generate_id(),
        'userId': user_id,
        'userName': user.get('name', 'Anonymous'),
        'projectId': project_id,
        'projectName': sanitize_string(data.get('projectName', '')),
        'description': sanitize_string(data.get('description', '')),
        'technologies': data.get('technologies', []),
        'screenshotUrl': sanitize_string(data.get('screenshotUrl', '')),
        'demoUrl': sanitize_string(data.get('demoUrl', '')),
        'githubUrl': sanitize_string(data.get('githubUrl', '')),
        'whatILearned': sanitize_string(data.get('whatILearned', '')),
        'challengesFaced': sanitize_string(data.get('challengesFaced', '')),
        'createdAt': now_iso()
    }

    showcases = read_json('showcases.json')
    showcases.append(showcase)
    write_json('showcases.json', showcases)

    return jsonify({'message': 'Showcase submitted', 'showcase': showcase}), 201


@showcase_bp.route('/user/<target_user_id>', methods=['GET'])
def user_showcases(target_user_id):
    """Get showcases for a specific user."""
    showcases = read_json('showcases.json')
    user_showcases = [s for s in showcases if s.get('userId') == target_user_id]
    return jsonify({'showcases': user_showcases}), 200
