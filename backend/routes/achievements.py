"""Achievements routes: list achievements, check unlocks, XP summary."""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.helpers import read_json, write_json, get_user_level, now_iso

achievements_bp = Blueprint('achievements', __name__)


@achievements_bp.route('', methods=['GET'])
@jwt_required()
def get_achievements():
    """Get all achievements with unlock status for current user."""
    user_id = get_jwt_identity()
    users = read_json('users.json')
    user = next((u for u in users if u['id'] == user_id), None)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    all_achievements = read_json('achievements.json')
    user_achievements = user.get('achievements', [])

    # Check and unlock new achievements
    newly_unlocked = []
    for ach in all_achievements:
        ach['unlocked'] = ach['id'] in user_achievements
        if not ach['unlocked']:
            if _check_criteria(ach, user):
                ach['unlocked'] = True
                newly_unlocked.append(ach['id'])

    # Save newly unlocked achievements
    if newly_unlocked:
        user_idx = next((i for i, u in enumerate(users) if u['id'] == user_id), None)
        if user_idx is not None:
            users[user_idx]['achievements'] = user_achievements + newly_unlocked
            # Award achievement XP
            for ach_id in newly_unlocked:
                ach_data = next((a for a in all_achievements if a['id'] == ach_id), None)
                if ach_data:
                    users[user_idx]['xp'] = users[user_idx].get('xp', 0) + ach_data.get('xpReward', 0)
            users[user_idx]['updatedAt'] = now_iso()
            write_json('users.json', users)

    return jsonify({'achievements': all_achievements, 'newlyUnlocked': newly_unlocked}), 200


@achievements_bp.route('/xp', methods=['GET'])
@jwt_required()
def xp_summary():
    """Get XP summary, level, and progress to next level."""
    user_id = get_jwt_identity()
    users = read_json('users.json')
    user = next((u for u in users if u['id'] == user_id), None)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    xp = user.get('xp', 0)
    xp_rules = read_json('xp_rules.json')
    current_level = get_user_level(xp, xp_rules)
    levels = xp_rules.get('levels', [])

    # Find next level
    next_level = None
    for lvl in levels:
        if lvl['minXP'] > xp:
            next_level = lvl
            break

    progress_to_next = 0
    if next_level and current_level:
        range_xp = next_level['minXP'] - current_level['minXP']
        progress_xp = xp - current_level['minXP']
        progress_to_next = round((progress_xp / range_xp * 100), 1) if range_xp > 0 else 100

    return jsonify({
        'xp': xp,
        'level': current_level,
        'nextLevel': next_level,
        'progressToNext': progress_to_next,
        'completedProjects': len(user.get('completedProjects', [])),
        'currentProjects': len(user.get('currentProjects', []))
    }), 200


def _check_criteria(achievement, user):
    """Check if user meets achievement criteria."""
    criteria = achievement.get('criteria', {})
    ctype = criteria.get('type', '')
    count = criteria.get('count', 0)

    if ctype == 'projects_completed':
        return len(user.get('completedProjects', [])) >= count
    elif ctype == 'debug_milestones':
        # Simplified: count total completed milestones
        total_milestones = sum(
            len(cp.get('completedMilestones', []))
            for cp in user.get('currentProjects', [])
        ) + sum(1 for _ in user.get('completedProjects', []))  # Approximate
        return total_milestones >= count
    elif ctype == 'active_days':
        return len(user.get('activeDays', [])) >= count
    elif ctype == 'copilot_used':
        return user.get('copilotUsed', False)
    elif ctype == 'domain_projects':
        # Check if 5 projects in any single domain
        projects = read_json('projects.json')
        completed_ids = user.get('completedProjects', [])
        domain_counts = {}
        for pid in completed_ids:
            proj = next((p for p in projects if p['id'] == pid), None)
            if proj:
                domain = proj.get('domain', '')
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
        return any(c >= count for c in domain_counts.values())
    elif ctype == 'fullstack_projects':
        return len(user.get('completedProjects', [])) >= count
    elif ctype == 'capstone_completed':
        projects = read_json('projects.json')
        completed_ids = user.get('completedProjects', [])
        capstones = [p for p in projects if p['id'] in completed_ids and p.get('level') == 10]
        return len(capstones) >= count

    return False
