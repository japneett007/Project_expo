"""Milestone routes: get content, update progress, mark complete."""
import random
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.helpers import read_json, write_json, now_iso, get_user_level

milestones_bp = Blueprint('milestones', __name__)


@milestones_bp.route('/project/<project_id>', methods=['GET'])
@jwt_required()
def get_project_milestones(project_id):
    """Get milestones for a project with user's progress status."""
    user_id = get_jwt_identity()
    users = read_json('users.json')
    user = next((u for u in users if u['id'] == user_id), None)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    projects = read_json('projects.json')
    project = next((p for p in projects if p['id'] == project_id), None)
    if not project:
        return jsonify({'error': 'Project not found'}), 404

    # Get milestone content
    all_milestones = read_json('milestones.json')
    milestone_ids = project.get('milestoneIds', [])

    # Get user's progress for this project
    user_project = next(
        (cp for cp in user.get('currentProjects', []) if cp['projectId'] == project_id), None
    )
    user_milestones = user_project.get('milestones', {}) if user_project else {}

    milestones = []
    for mid in milestone_ids:
        milestone_data = next((m for m in all_milestones if m.get('id') == mid), None)
        if milestone_data:
            milestone_data['status'] = user_milestones.get(mid, 'locked')
        else:
            # Generate basic milestone info from ID
            milestone_data = {
                'id': mid,
                'title': mid.replace('-', ' ').title(),
                'status': user_milestones.get(mid, 'locked')
            }
        milestones.append(milestone_data)

    completed = len([m for m in milestones if m.get('status') == 'completed'])
    total = len(milestones)
    progress = round((completed / total * 100), 1) if total > 0 else 0

    return jsonify({
        'projectId': project_id,
        'milestones': milestones,
        'progress': progress,
        'completed': completed,
        'total': total
    }), 200


@milestones_bp.route('/<milestone_id>/complete', methods=['PUT'])
@jwt_required()
def complete_milestone(milestone_id):
    """Mark a milestone as complete — server-validated."""
    user_id = get_jwt_identity()
    users = read_json('users.json')
    user_idx = next((i for i, u in enumerate(users) if u['id'] == user_id), None)
    if user_idx is None:
        return jsonify({'error': 'User not found'}), 404

    user = users[user_idx]

    # Find which project this milestone belongs to
    project_found = False
    for i, cp in enumerate(user.get('currentProjects', [])):
        if milestone_id in cp.get('milestones', {}):
            project_found = True
            project_idx = i
            break

    if not project_found:
        return jsonify({'error': 'Milestone not found in your projects'}), 404

    user_project = user['currentProjects'][project_idx]
    current_status = user_project['milestones'].get(milestone_id)

    if current_status == 'completed':
        return jsonify({'message': 'Milestone already completed'}), 200
    if current_status == 'locked':
        return jsonify({'error': 'Milestone is locked'}), 403

    # Mark as completed
    user_project['milestones'][milestone_id] = 'completed'
    if milestone_id not in user_project['completedMilestones']:
        user_project['completedMilestones'].append(milestone_id)

    # Unlock next milestone
    projects = read_json('projects.json')
    project = next((p for p in projects if p['id'] == user_project['projectId']), None)
    if project:
        milestone_ids = project.get('milestoneIds', [])
        current_idx = milestone_ids.index(milestone_id) if milestone_id in milestone_ids else -1
        if current_idx >= 0 and current_idx + 1 < len(milestone_ids):
            next_mid = milestone_ids[current_idx + 1]
            if user_project['milestones'].get(next_mid) == 'locked':
                user_project['milestones'][next_mid] = 'available'

    # Calculate progress
    total = len(user_project['milestones'])
    completed = len(user_project['completedMilestones'])
    user_project['progress'] = round((completed / total * 100), 1) if total > 0 else 0

    # Award XP (server-side calculation)
    xp_rules = read_json('xp_rules.json')
    xp_gained = xp_rules.get('complete_learning_milestone', 10)

    # Check if it's a major milestone (every 3rd or final)
    if completed % 3 == 0 or completed == total:
        xp_gained = xp_rules.get('complete_major_milestone', 25)

    user['xp'] = user.get('xp', 0) + xp_gained

    # Track active day for achievements
    today = now_iso()[:10]
    if today not in user.get('activeDays', []):
        user['activeDays'] = user.get('activeDays', []) + [today]

    # Check for project completion
    project_completed = False
    motivation_message = None
    messages = read_json('motivational_messages.json')

    if user_project['progress'] >= 100:
        project_completed = True
        # Move to completed projects
        user['completedProjects'] = user.get('completedProjects', []) + [user_project['projectId']]
        user['currentProjects'].pop(project_idx)

        # Award project completion XP based on difficulty
        if project:
            difficulty = project.get('difficulty', 'beginner')
            level = project.get('level', 1)
            if level == 10:
                user['xp'] += xp_rules.get('complete_capstone', 400)
            elif difficulty == 'advanced' or level >= 6:
                user['xp'] += xp_rules.get('complete_advanced_project', 250)
            elif difficulty == 'intermediate' or level >= 4:
                user['xp'] += xp_rules.get('complete_intermediate_project', 150)
            else:
                user['xp'] += xp_rules.get('complete_beginner_project', 100)

        motivation_message = random.choice(messages.get('project_complete_messages', ['🎉 Project complete!']))
    else:
        user['currentProjects'][project_idx] = user_project
        motivation_message = random.choice(messages.get('milestone_messages', ['Keep going!']))

    # Calculate level
    level_info = get_user_level(user['xp'], xp_rules)

    user['updatedAt'] = now_iso()
    users[user_idx] = user
    write_json('users.json', users)

    return jsonify({
        'message': 'Milestone completed',
        'xpGained': xp_gained,
        'totalXP': user['xp'],
        'level': level_info,
        'progress': user_project['progress'] if not project_completed else 100,
        'projectCompleted': project_completed,
        'motivationMessage': motivation_message
    }), 200


@milestones_bp.route('/<milestone_id>', methods=['GET'])
def get_milestone_content(milestone_id):
    """Get full milestone content (concept, explanation, implementation, etc.)."""
    all_milestones = read_json('milestones.json')
    milestone = next((m for m in all_milestones if m.get('id') == milestone_id), None)

    if not milestone:
        # Return a generated basic milestone
        return jsonify({
            'milestone': {
                'id': milestone_id,
                'title': milestone_id.replace('-', ' ').title(),
                'objective': 'Complete this milestone to progress in your project.',
                'why': 'This step builds on previous work and prepares you for the next milestone.',
                'concept': 'Apply the concepts learned so far.',
                'explanation': 'Review the instructions and implement the required functionality.',
                'implementation': 'Follow the step-by-step guide in your project workspace.',
                'expectedResult': 'Your implementation should work as described.',
                'verification': 'Test your code and verify the expected output.',
                'commonErrors': ['Check for syntax errors', 'Verify variable names', 'Check imports'],
                'debugging': 'Use console.log or print statements to trace issues.'
            }
        }), 200

    return jsonify({'milestone': milestone}), 200
