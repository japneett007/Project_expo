"""Project discovery, detail and recommendation routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.helpers import read_json, write_json, now_iso

projects_bp = Blueprint('projects', __name__)


@projects_bp.route('', methods=['GET'])
def list_projects():
    """List projects with filtering: domain, difficulty, branch, type, search."""
    projects = read_json('projects.json')

    # Filters
    domain = request.args.get('domain')
    difficulty = request.args.get('difficulty')
    branch = request.args.get('branch')
    project_type = request.args.get('type')
    search = request.args.get('search', '').lower()

    if domain:
        projects = [p for p in projects if p['domain'] == domain]
    if difficulty:
        projects = [p for p in projects if p['difficulty'] == difficulty]
    if branch:
        projects = [p for p in projects if branch in p.get('branches', [])]
    if project_type:
        projects = [p for p in projects if p.get('type', '').lower() == project_type.lower()]
    if search:
        projects = [p for p in projects if
                    search in p['title'].lower() or
                    search in p.get('description', '').lower() or
                    any(search in t.lower() for t in p.get('technologies', []))]

    # Sort by level
    sort_by = request.args.get('sort', 'level')
    if sort_by == 'level':
        projects.sort(key=lambda p: p.get('level', 0))
    elif sort_by == 'title':
        projects.sort(key=lambda p: p['title'].lower())

    return jsonify({'projects': projects, 'total': len(projects)}), 200


@projects_bp.route('/<project_id>', methods=['GET'])
def get_project(project_id):
    """Get detailed project information."""
    projects = read_json('projects.json')
    project = next((p for p in projects if p['id'] == project_id), None)
    if not project:
        return jsonify({'error': 'Project not found'}), 404

    # Attach prerequisites
    prereqs = read_json('prerequisites.json')
    project['prerequisiteDetails'] = prereqs.get(project_id, {'required': [], 'recommended': []})

    return jsonify({'project': project}), 200


@projects_bp.route('/<project_id>/start', methods=['POST'])
@jwt_required()
def start_project(project_id):
    """Start a project for the current user."""
    user_id = get_jwt_identity()
    users = read_json('users.json')
    user_idx = next((i for i, u in enumerate(users) if u['id'] == user_id), None)
    if user_idx is None:
        return jsonify({'error': 'User not found'}), 404

    user = users[user_idx]
    projects = read_json('projects.json')
    project = next((p for p in projects if p['id'] == project_id), None)
    if not project:
        return jsonify({'error': 'Project not found'}), 404

    # Check if already started
    if any(cp['projectId'] == project_id for cp in user.get('currentProjects', [])):
        return jsonify({'message': 'Project already started'}), 200

    # Check if already completed
    if project_id in user.get('completedProjects', []):
        return jsonify({'message': 'Project already completed'}), 200

    # Add to current projects with milestone tracking
    milestone_ids = project.get('milestoneIds', [])
    user_project = {
        'projectId': project_id,
        'startedAt': now_iso(),
        'milestones': {mid: 'locked' for mid in milestone_ids},
        'completedMilestones': [],
        'progress': 0
    }
    # Unlock first milestone
    if milestone_ids:
        user_project['milestones'][milestone_ids[0]] = 'available'

    user['currentProjects'].append(user_project)
    user['updatedAt'] = now_iso()
    users[user_idx] = user
    write_json('users.json', users)

    return jsonify({'message': 'Project started', 'userProject': user_project}), 201


@projects_bp.route('/recommended', methods=['GET'])
@jwt_required()
def recommended_projects():
    """Get personalized project recommendations based on user profile."""
    user_id = get_jwt_identity()
    users = read_json('users.json')
    user = next((u for u in users if u['id'] == user_id), None)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    projects = read_json('projects.json')
    completed_ids = user.get('completedProjects', [])
    current_ids = [cp['projectId'] for cp in user.get('currentProjects', [])]
    interested_domains = user.get('interestedDomains', [])
    branch = user.get('branch', '')
    skill_level = user.get('skillLevel', 'beginner')

    # Filter out completed and current
    available = [p for p in projects if p['id'] not in completed_ids and p['id'] not in current_ids]

    # Score projects based on user profile
    scored = []
    for p in available:
        score = 0
        # Domain match
        if p['domain'] in interested_domains:
            score += 30
        # Branch match
        if branch in p.get('branches', []):
            score += 20
        # Skill level match
        skill_map = {'beginner': [1, 2, 3], 'intermediate': [3, 4, 5, 6], 'advanced': [6, 7, 8, 9, 10]}
        if p.get('level', 1) in skill_map.get(skill_level, [1, 2, 3]):
            score += 25
        # Prerequisites met
        prereq_projects = p.get('prerequisites', [])
        if all(pid in completed_ids for pid in prereq_projects):
            score += 25
        elif not prereq_projects:
            score += 15

        scored.append({**p, '_score': score})

    scored.sort(key=lambda x: x['_score'], reverse=True)

    # Return top 10 recommendations
    recommendations = [{k: v for k, v in p.items() if k != '_score'} for p in scored[:10]]

    return jsonify({'recommendations': recommendations}), 200


@projects_bp.route('/domains', methods=['GET'])
def list_domains():
    """List all available domains."""
    domains = read_json('domains.json')
    return jsonify({'domains': domains}), 200


@projects_bp.route('/branches', methods=['GET'])
def list_branches():
    """List all available academic branches."""
    branches = read_json('branches.json')
    return jsonify({'branches': branches}), 200
