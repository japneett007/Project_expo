"""Community routes: discussions, answers, upvotes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.helpers import read_json, write_json, generate_id, now_iso, sanitize_string

community_bp = Blueprint('community', __name__)


@community_bp.route('/<project_id>', methods=['GET'])
def get_discussions(project_id):
    """Get discussions for a specific project."""
    discussions = read_json('discussions.json')
    project_discussions = [d for d in discussions if d.get('projectId') == project_id]
    project_discussions.sort(key=lambda d: d.get('createdAt', ''), reverse=True)
    return jsonify({'discussions': project_discussions}), 200


@community_bp.route('/<project_id>', methods=['POST'])
@jwt_required()
def create_discussion(project_id):
    """Create a new discussion or answer."""
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    content = sanitize_string(data.get('content', ''))
    title = sanitize_string(data.get('title', ''))
    parent_id = data.get('parentId')  # If answering an existing discussion

    if not content:
        return jsonify({'error': 'Content is required'}), 400

    users = read_json('users.json')
    user = next((u for u in users if u['id'] == user_id), None)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    discussions = read_json('discussions.json')

    discussion = {
        'id': generate_id(),
        'projectId': project_id,
        'userId': user_id,
        'userName': user.get('name', 'Anonymous'),
        'title': title,
        'content': content,
        'parentId': parent_id,
        'upvotes': 0,
        'upvotedBy': [],
        'createdAt': now_iso()
    }

    discussions.append(discussion)
    write_json('discussions.json', discussions)

    # Award XP for helpful answer
    if parent_id:
        xp_rules = read_json('xp_rules.json')
        user_idx = next((i for i, u in enumerate(users) if u['id'] == user_id), None)
        if user_idx is not None:
            users[user_idx]['xp'] = users[user_idx].get('xp', 0) + xp_rules.get('helpful_community_answer', 15)
            users[user_idx]['updatedAt'] = now_iso()
            write_json('users.json', users)

    return jsonify({'message': 'Posted successfully', 'discussion': discussion}), 201


@community_bp.route('/upvote/<discussion_id>', methods=['POST'])
@jwt_required()
def upvote(discussion_id):
    """Upvote a discussion/answer."""
    user_id = get_jwt_identity()
    discussions = read_json('discussions.json')
    disc_idx = next((i for i, d in enumerate(discussions) if d['id'] == discussion_id), None)

    if disc_idx is None:
        return jsonify({'error': 'Discussion not found'}), 404

    disc = discussions[disc_idx]

    # Prevent self-upvote
    if disc['userId'] == user_id:
        return jsonify({'error': 'Cannot upvote your own post'}), 400

    # Prevent duplicate upvote
    if user_id in disc.get('upvotedBy', []):
        return jsonify({'error': 'Already upvoted'}), 400

    disc['upvotes'] = disc.get('upvotes', 0) + 1
    disc['upvotedBy'] = disc.get('upvotedBy', []) + [user_id]
    discussions[disc_idx] = disc
    write_json('discussions.json', discussions)

    # Award XP to the author
    xp_rules = read_json('xp_rules.json')
    users = read_json('users.json')
    author_idx = next((i for i, u in enumerate(users) if u['id'] == disc['userId']), None)
    if author_idx is not None:
        users[author_idx]['xp'] = users[author_idx].get('xp', 0) + xp_rules.get('answer_upvoted', 5)
        users[author_idx]['updatedAt'] = now_iso()
        write_json('users.json', users)

    return jsonify({'message': 'Upvoted', 'upvotes': disc['upvotes']}), 200
