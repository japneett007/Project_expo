"""Leaderboard routes: global, branch, domain, weekly, all-time rankings."""
from flask import Blueprint, request, jsonify
from utils.helpers import read_json, get_user_level

leaderboard_bp = Blueprint('leaderboard', __name__)


@leaderboard_bp.route('', methods=['GET'])
def get_leaderboard():
    """Get rankings with optional filters."""
    ranking_type = request.args.get('type', 'global')  # global, branch, domain, weekly
    branch = request.args.get('branch', '')
    domain = request.args.get('domain', '')

    users = read_json('users.json')
    xp_rules = read_json('xp_rules.json')

    # Build leaderboard entries
    entries = []
    for user in users:
        if user.get('xp', 0) == 0:
            continue

        # Apply filters
        if ranking_type == 'branch' and branch:
            if user.get('branch', '') != branch:
                continue
        elif ranking_type == 'domain' and domain:
            # Filter users who have completed projects in this domain
            projects = read_json('projects.json')
            completed_ids = user.get('completedProjects', [])
            domain_projects = [p for p in projects if p['id'] in completed_ids and p.get('domain') == domain]
            if not domain_projects:
                continue

        level_info = get_user_level(user.get('xp', 0), xp_rules)
        entries.append({
            'userId': user['id'],
            'name': user.get('name', 'Anonymous'),
            'xp': user.get('xp', 0),
            'level': level_info.get('level', 1),
            'levelName': level_info.get('name', 'Explorer'),
            'completedProjects': len(user.get('completedProjects', [])),
            'branch': user.get('branch', ''),
            'profileImage': user.get('profileImage', '')
        })

    # Sort by XP descending
    entries.sort(key=lambda e: e['xp'], reverse=True)

    # Add rank
    for i, entry in enumerate(entries):
        entry['rank'] = i + 1

    return jsonify({
        'leaderboard': entries[:50],  # Top 50
        'type': ranking_type,
        'total': len(entries)
    }), 200
