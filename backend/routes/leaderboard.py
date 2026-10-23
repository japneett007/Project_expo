"""Leaderboard routes: global, branch, domain rankings — reads from SQLite."""
from flask import Blueprint, request, jsonify

from database import get_db, get_user_level_from_db
from models import User, UserProject

leaderboard_bp = Blueprint('leaderboard', __name__)


@leaderboard_bp.route('', methods=['GET'])
def get_leaderboard():
    """Get rankings with optional filters (type, branch, domain)."""
    ranking_type = request.args.get('type', 'global')
    branch = request.args.get('branch', '')
    domain = request.args.get('domain', '')

    with get_db() as db:
        # Fetch all users with XP > 0
        q = db.query(User).filter(User.xp > 0)

        if ranking_type == 'branch' and branch:
            q = q.filter(User.branch_id == branch)

        users = q.all()

        # For domain filter we need to check completed projects in that domain
        if ranking_type == 'domain' and domain:
            from models import Project
            filtered = []
            for u in users:
                has_domain_project = (
                    db.query(UserProject)
                    .join(Project, Project.id == UserProject.project_id)
                    .filter(
                        UserProject.user_id == u.id,
                        UserProject.status == 'completed',
                        Project.domain_id == domain,
                    )
                    .first()
                )
                if has_domain_project:
                    filtered.append(u)
            users = filtered

        entries = []
        for u in users:
            level_info = get_user_level_from_db(u.xp, db)
            completed_count = (
                db.query(UserProject)
                .filter(UserProject.user_id == u.id, UserProject.status == 'completed')
                .count()
            )
            entries.append({
                'userId': u.id,
                'name': u.name,
                'xp': u.xp,
                'level': level_info['level'],
                'levelName': level_info['name'],
                'completedProjects': completed_count,
                'branch': u.branch_id or '',
                'profileImage': u.profile_image or '',
            })

    # Sort by XP descending, add rank
    entries.sort(key=lambda e: e['xp'], reverse=True)
    for i, entry in enumerate(entries):
        entry['rank'] = i + 1

    return jsonify({
        'leaderboard': entries[:50],
        'type': ranking_type,
        'total': len(entries),
    }), 200
