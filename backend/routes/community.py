"""Community routes: discussions, replies, upvotes — SQLite."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from database import get_db
from models import Discussion, DiscussionUpvote, User, XpActionRule
from utils.helpers import generate_id, now_iso, sanitize_string

community_bp = Blueprint('community', __name__)


# ── Serialiser ─────────────────────────────────────────────────────────────────

def _disc_to_dict(d, upvoted_by):
    return {
        'id': d.id,
        'projectId': d.project_id,
        'userId': d.user_id,
        'userName': d.user_name,
        'title': d.title or '',
        'content': d.content,
        'parentId': d.parent_id,
        'upvotes': d.upvotes,
        'upvotedBy': upvoted_by,
        'createdAt': d.created_at,
    }


def _get_upvoted_by(db, discussion_id):
    return [
        row.user_id
        for row in db.query(DiscussionUpvote)
        .filter(DiscussionUpvote.discussion_id == discussion_id)
        .all()
    ]


# ── Routes ─────────────────────────────────────────────────────────────────────

@community_bp.route('/<project_id>', methods=['GET'])
def get_discussions(project_id):
    """Get discussions for a specific project, newest first."""
    with get_db() as db:
        discs = (
            db.query(Discussion)
            .filter(Discussion.project_id == project_id)
            .order_by(Discussion.created_at.desc())
            .all()
        )
        result = [_disc_to_dict(d, _get_upvoted_by(db, d.id)) for d in discs]
    return jsonify({'discussions': result}), 200


@community_bp.route('/<project_id>', methods=['POST'])
@jwt_required()
def create_discussion(project_id):
    """Create a new discussion or reply."""
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body required'}), 400

    content = sanitize_string(data.get('content', ''))
    title = sanitize_string(data.get('title', ''))
    parent_id = data.get('parentId')

    if not content:
        return jsonify({'error': 'Content is required'}), 400

    with get_db() as db:
        user = db.get(User, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        disc = Discussion(
            id=generate_id(),
            project_id=project_id,
            user_id=user_id,
            user_name=user.name,
            title=title,
            content=content,
            parent_id=parent_id,
            upvotes=0,
            created_at=now_iso(),
        )
        db.add(disc)
        db.flush()

        # Award XP for helpful reply
        if parent_id:
            rule = db.get(XpActionRule, 'helpful_community_answer')
            xp_gain = rule.xp_value if rule else 15
            user.xp = (user.xp or 0) + xp_gain
            user.updated_at = now_iso()

        result = _disc_to_dict(disc, [])

    return jsonify({'message': 'Posted successfully', 'discussion': result}), 201


@community_bp.route('/upvote/<discussion_id>', methods=['POST'])
@jwt_required()
def upvote(discussion_id):
    """Upvote a discussion. Prevents self-upvotes and duplicates."""
    user_id = get_jwt_identity()

    with get_db() as db:
        disc = db.get(Discussion, discussion_id)
        if not disc:
            return jsonify({'error': 'Discussion not found'}), 404

        if disc.user_id == user_id:
            return jsonify({'error': 'Cannot upvote your own post'}), 400

        existing = db.get(DiscussionUpvote, (discussion_id, user_id))
        if existing:
            return jsonify({'error': 'Already upvoted'}), 400

        db.add(DiscussionUpvote(discussion_id=discussion_id, user_id=user_id))
        disc.upvotes = (disc.upvotes or 0) + 1

        # Award XP to the author
        author = db.get(User, disc.user_id)
        if author:
            rule = db.get(XpActionRule, 'answer_upvoted')
            xp_gain = rule.xp_value if rule else 5
            author.xp = (author.xp or 0) + xp_gain
            author.updated_at = now_iso()

        upvotes = disc.upvotes

    return jsonify({'message': 'Upvoted', 'upvotes': upvotes}), 200
