"""Milestone routes: get content, update progress, mark complete — SQLite."""
import json
import random

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from database import get_db, get_user_level_from_db
from models import (
    Milestone, Project, User,
    UserProject, UserProjectMilestone, XpActionRule,
    MotivationalMessage,
)
from utils.helpers import now_iso

milestones_bp = Blueprint('milestones', __name__)


# ── Serialisers ────────────────────────────────────────────────────────────────

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


def _milestone_to_dict(m, status='available'):
    return {
        'id': m.id,
        'projectId': m.project_id,
        'title': m.title,
        'objective': m.objective or '',
        'why': m.why or '',
        'concept': m.concept or '',
        'explanation': m.explanation or '',
        'implementation': m.implementation or '',
        'expectedResult': m.expected_result or '',
        'verification': m.verification or '',
        'commonErrors': _parse(m.common_errors),
        'debugging': m.debugging or '',
        'sortOrder': m.sort_order,
        'status': status,
    }


def _stub_milestone(milestone_id, status='available'):
    """Fallback when a milestone has no DB content (milestones.json was empty)."""
    return {
        'id': milestone_id,
        'projectId': '',
        'title': milestone_id.replace('-', ' ').title(),
        'objective': 'Complete this milestone to progress in your project.',
        'why': 'This step builds on previous work and prepares you for the next milestone.',
        'concept': 'Apply the concepts learned so far.',
        'explanation': 'Review the instructions and implement the required functionality.',
        'implementation': 'Follow the step-by-step guide in your project workspace.',
        'expectedResult': 'Your implementation should work as described.',
        'verification': 'Test your code and verify the expected output.',
        'commonErrors': ['Check for syntax errors', 'Verify variable names', 'Check imports'],
        'debugging': 'Use console.log or print statements to trace issues.',
        'sortOrder': 0,
        'status': status,
    }


def _xp_rule(db, action, default=0):
    rule = db.get(XpActionRule, action)
    return rule.xp_value if rule else default


def _random_message(db, category, fallback=''):
    msgs = (
        db.query(MotivationalMessage)
        .filter(MotivationalMessage.category == category)
        .all()
    )
    if msgs:
        return random.choice(msgs).message
    return fallback


# ── Routes ─────────────────────────────────────────────────────────────────────

@milestones_bp.route('/project/<project_id>', methods=['GET'])
@jwt_required()
def get_project_milestones(project_id):
    """Get milestones for a project with the user's progress status."""
    user_id = get_jwt_identity()

    with get_db() as db:
        user = db.get(User, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        project = db.get(Project, project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404

        milestone_ids = _parse(project.milestone_ids)

        # User's milestone statuses for this project
        ms_rows = (
            db.query(UserProjectMilestone)
            .filter(
                UserProjectMilestone.user_id == user_id,
                UserProjectMilestone.project_id == project_id,
            )
            .all()
        )
        status_map = {row.milestone_id: row.status for row in ms_rows}

        milestones = []
        for mid in milestone_ids:
            status = status_map.get(mid, 'locked')
            m = db.get(Milestone, mid)
            if m:
                milestones.append(_milestone_to_dict(m, status))
            else:
                milestones.append(_stub_milestone(mid, status))

        completed = sum(1 for m in milestones if m['status'] == 'completed')
        total = len(milestones)
        progress = round((completed / total * 100), 1) if total > 0 else 0

        # Also get progress from user_projects table (authoritative)
        up = (
            db.query(UserProject)
            .filter(UserProject.user_id == user_id, UserProject.project_id == project_id)
            .first()
        )
        if up:
            progress = up.progress or progress

    return jsonify({
        'projectId': project_id,
        'milestones': milestones,
        'progress': progress,
        'completed': completed,
        'total': total,
    }), 200


@milestones_bp.route('/<milestone_id>/complete', methods=['PUT'])
@jwt_required()
def complete_milestone(milestone_id):
    """Mark a milestone as complete — server-validated."""
    user_id = get_jwt_identity()

    with get_db() as db:
        user = db.get(User, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Find the UserProjectMilestone row for this milestone
        upm = (
            db.query(UserProjectMilestone)
            .filter(
                UserProjectMilestone.user_id == user_id,
                UserProjectMilestone.milestone_id == milestone_id,
            )
            .first()
        )
        if not upm:
            return jsonify({'error': 'Milestone not found in your projects'}), 404

        if upm.status == 'completed':
            return jsonify({'message': 'Milestone already completed'}), 200
        if upm.status == 'locked':
            return jsonify({'error': 'Milestone is locked'}), 403

        # Mark this milestone completed
        upm.status = 'completed'

        # Unlock next milestone in the project's sequence
        project = db.get(Project, upm.project_id)
        milestone_ids = _parse(project.milestone_ids) if project else []
        if milestone_id in milestone_ids:
            current_idx = milestone_ids.index(milestone_id)
            next_idx = current_idx + 1
            if next_idx < len(milestone_ids):
                next_mid = milestone_ids[next_idx]
                next_upm = (
                    db.query(UserProjectMilestone)
                    .filter(
                        UserProjectMilestone.user_id == user_id,
                        UserProjectMilestone.project_id == upm.project_id,
                        UserProjectMilestone.milestone_id == next_mid,
                    )
                    .first()
                )
                if next_upm and next_upm.status == 'locked':
                    next_upm.status = 'available'

        # Recalculate progress
        all_ms = (
            db.query(UserProjectMilestone)
            .filter(
                UserProjectMilestone.user_id == user_id,
                UserProjectMilestone.project_id == upm.project_id,
            )
            .all()
        )
        total_ms = len(all_ms)
        completed_ms = sum(1 for row in all_ms if row.status == 'completed')
        new_progress = round((completed_ms / total_ms * 100), 1) if total_ms > 0 else 0

        up = (
            db.query(UserProject)
            .filter(
                UserProject.user_id == user_id,
                UserProject.project_id == upm.project_id,
            )
            .first()
        )
        if up:
            up.progress = new_progress

        # Award XP
        xp_gained = _xp_rule(db, 'complete_learning_milestone', 10)
        if completed_ms % 3 == 0 or completed_ms == total_ms:
            xp_gained = _xp_rule(db, 'complete_major_milestone', 25)

        user.xp = (user.xp or 0) + xp_gained

        # Track active day
        today = now_iso()[:10]
        try:
            active_days = json.loads(user.active_days) if isinstance(user.active_days, str) else []
        except (ValueError, TypeError):
            active_days = []
        if today not in active_days:
            active_days.append(today)
            user.active_days = json.dumps(active_days, ensure_ascii=False)

        # Check project completion
        project_completed = False
        motivation_message = None

        if new_progress >= 100:
            project_completed = True
            if up:
                up.status = 'completed'

            # Award project-completion XP
            if project:
                difficulty = project.difficulty
                level = project.level
                if level == 10:
                    user.xp += _xp_rule(db, 'complete_capstone', 400)
                elif difficulty == 'advanced' or level >= 6:
                    user.xp += _xp_rule(db, 'complete_advanced_project', 250)
                elif difficulty == 'intermediate' or level >= 4:
                    user.xp += _xp_rule(db, 'complete_intermediate_project', 150)
                else:
                    user.xp += _xp_rule(db, 'complete_beginner_project', 100)

            motivation_message = _random_message(
                db, 'project_complete', '🎉 Project complete!'
            )
        else:
            motivation_message = _random_message(
                db, 'milestone', 'Keep going! 🔥'
            )

        user.updated_at = now_iso()
        level_info = get_user_level_from_db(user.xp, db)
        final_progress = 100 if project_completed else new_progress

        # Capture primitive values before session closes
        _xp_gained = xp_gained
        _total_xp = user.xp
        _level_info = level_info
        _progress = final_progress
        _project_completed = project_completed
        _motivation_message = motivation_message

    return jsonify({
        'message': 'Milestone completed',
        'xpGained': _xp_gained,
        'totalXP': _total_xp,
        'level': _level_info,
        'progress': _progress,
        'projectCompleted': _project_completed,
        'motivationMessage': _motivation_message,
    }), 200


@milestones_bp.route('/<milestone_id>', methods=['GET'])
def get_milestone_content(milestone_id):
    """Get full milestone content."""
    with get_db() as db:
        m = db.get(Milestone, milestone_id)
        if not m:
            return jsonify({'milestone': _stub_milestone(milestone_id, 'available')}), 200
        data = _milestone_to_dict(m, 'available')

    return jsonify({'milestone': data}), 200
