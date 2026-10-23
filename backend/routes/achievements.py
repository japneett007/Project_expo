import json

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from database import get_db
from models import Achievement, User, UserAchievement, UserProject, XpLevel
from utils.helpers import now_iso

achievements_bp = Blueprint('achievements', __name__)


# ── Serialisers ────────────────────────────────────────────────────────────────

def _ach_to_dict(ach, unlocked=False):
    return ach.to_dict(unlocked=unlocked)


# ── Routes ─────────────────────────────────────────────────────────────────────

@achievements_bp.route('', methods=['GET'])
@jwt_required()
def get_achievements():
    """Get all achievements with unlock status for current user."""
    user_id = get_jwt_identity()

    with get_db() as db:
        user = db.get(User, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        all_achievements = db.query(Achievement).order_by(Achievement.name).all()

        # IDs already unlocked
        unlocked_ids = {
            ua.achievement_id
            for ua in db.query(UserAchievement)
            .filter(UserAchievement.user_id == user_id)
            .all()
        }

        # Check for new unlocks
        newly_unlocked = []
        for ach in all_achievements:
            if ach.id not in unlocked_ids and _check_criteria(ach, user, db):
                unlocked_ids.add(ach.id)
                newly_unlocked.append(ach.id)
                # Record in DB
                db.add(UserAchievement(
                    user_id=user_id,
                    achievement_id=ach.id,
                    unlocked_at=now_iso(),
                ))
                # Award XP
                user.xp = (user.xp or 0) + ach.xp_reward

        if newly_unlocked:
            user.updated_at = now_iso()

        result = [_ach_to_dict(a, a.id in unlocked_ids) for a in all_achievements]

    return jsonify({'achievements': result, 'newlyUnlocked': newly_unlocked}), 200


@achievements_bp.route('/xp', methods=['GET'])
@jwt_required()
def xp_summary():
    """Get XP summary, level, and progress to next level."""
    user_id = get_jwt_identity()

    with get_db() as db:
        user = db.get(User, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        xp = user.xp or 0
        levels = db.query(XpLevel).order_by(XpLevel.level).all()

        current_level = {'level': 1, 'name': 'Explorer', 'minXP': 0}
        next_level = None
        for lvl in levels:
            if xp >= lvl.min_xp:
                current_level = {'level': lvl.level, 'name': lvl.name, 'minXP': lvl.min_xp}
            elif next_level is None:
                next_level = {'level': lvl.level, 'name': lvl.name, 'minXP': lvl.min_xp}

        progress_to_next = 0
        if next_level:
            range_xp = next_level['minXP'] - current_level['minXP']
            progress_xp = xp - current_level['minXP']
            progress_to_next = round((progress_xp / range_xp * 100), 1) if range_xp > 0 else 100

        completed = (
            db.query(UserProject)
            .filter(UserProject.user_id == user_id, UserProject.status == 'completed')
            .count()
        )
        current = (
            db.query(UserProject)
            .filter(UserProject.user_id == user_id, UserProject.status == 'active')
            .count()
        )

    return jsonify({
        'xp': xp,
        'level': current_level,
        'nextLevel': next_level,
        'progressToNext': progress_to_next,
        'completedProjects': completed,
        'currentProjects': current,
    }), 200


# ── Criteria checker ───────────────────────────────────────────────────────────

def _check_criteria(achievement, user, db):
    """Return True if the user meets the achievement's unlock criteria."""
    try:
        criteria = json.loads(achievement.criteria) if isinstance(achievement.criteria, str) else {}
    except (ValueError, TypeError):
        criteria = {}

    ctype = criteria.get('type', '')
    count = criteria.get('count', 0)

    if ctype == 'projects_completed':
        completed = (
            db.query(UserProject)
            .filter(UserProject.user_id == user.id, UserProject.status == 'completed')
            .count()
        )
        return completed >= count

    elif ctype == 'debug_milestones':
        from models import UserProjectMilestone
        total_ms = (
            db.query(UserProjectMilestone)
            .filter(
                UserProjectMilestone.user_id == user.id,
                UserProjectMilestone.status == 'completed',
            )
            .count()
        )
        return total_ms >= count

    elif ctype == 'active_days':
        import json as _json
        try:
            days = _json.loads(user.active_days) if isinstance(user.active_days, str) else []
        except (ValueError, TypeError):
            days = []
        return len(days) >= count

    elif ctype == 'copilot_used':
        return bool(user.copilot_used)

    elif ctype == 'domain_projects':
        from models import Project
        domain_rows = (
            db.query(Project.domain_id)
            .join(UserProject, UserProject.project_id == Project.id)
            .filter(
                UserProject.user_id == user.id,
                UserProject.status == 'completed',
            )
            .all()
        )
        from collections import Counter
        counts = Counter(r[0] for r in domain_rows)
        return any(c >= count for c in counts.values())

    elif ctype in ('fullstack_projects', 'capstone_completed'):
        if ctype == 'fullstack_projects':
            completed = (
                db.query(UserProject)
                .filter(UserProject.user_id == user.id, UserProject.status == 'completed')
                .count()
            )
            return completed >= count
        else:  # capstone_completed
            from models import Project
            capstones = (
                db.query(UserProject)
                .join(Project, Project.id == UserProject.project_id)
                .filter(
                    UserProject.user_id == user.id,
                    UserProject.status == 'completed',
                    Project.level == 10,
                )
                .count()
            )
            return capstones >= count

    return False
