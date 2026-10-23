"""Project discovery, detail, recommendation and start routes — SQLite."""
import json

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from database import get_db
from models import (
    Domain, Branch, Project, ProjectPrerequisite,
    User, UserProject, UserProjectMilestone,
)
from utils.helpers import now_iso

projects_bp = Blueprint('projects', __name__)


# ── Serialisers ────────────────────────────────────────────────────────────────

def _parse_json_field(value, default=None):
    """Safely parse a JSON text column; return default on failure."""
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


def _project_to_dict(p: Project) -> dict:
    return {
        'id': p.id,
        'domain': p.domain_id,          # frontend uses p.domain
        'title': p.title,
        'difficulty': p.difficulty,
        'level': p.level,
        'type': p.type,
        'branches': _parse_json_field(p.branches),
        'technologies': _parse_json_field(p.technologies),
        'description': p.description,
        'whyBuildThis': p.why_build_this,
        'whatYouLearn': _parse_json_field(p.what_you_learn),
        'prerequisites': _parse_json_field(p.prerequisites),
        'estimatedHours': p.estimated_hours,
        'milestoneIds': _parse_json_field(p.milestone_ids),
    }


def _domain_to_dict(d: Domain) -> dict:
    return {'id': d.id, 'name': d.name, 'icon': d.icon or '', 'color': d.color or '', 'description': d.description or ''}


def _branch_to_dict(b: Branch) -> dict:
    return {'id': b.id, 'name': b.name, 'shortName': b.short_name}


# ── Routes ─────────────────────────────────────────────────────────────────────

@projects_bp.route('', methods=['GET'])
def list_projects():
    """List projects with filtering: domain, difficulty, branch, type, search."""
    domain = request.args.get('domain')
    difficulty = request.args.get('difficulty')
    branch = request.args.get('branch')
    project_type = request.args.get('type')
    search = request.args.get('search', '').lower()
    sort_by = request.args.get('sort', 'level')

    with get_db() as db:
        q = db.query(Project)
        if domain:
            q = q.filter(Project.domain_id == domain)
        if difficulty:
            q = q.filter(Project.difficulty == difficulty)

        projects = q.all()

        # Post-filter for JSON-text fields
        if branch:
            projects = [p for p in projects if branch in _parse_json_field(p.branches)]
        if project_type:
            projects = [p for p in projects if p.type.lower() == project_type.lower()]
        if search:
            projects = [
                p for p in projects
                if search in p.title.lower()
                or search in (p.description or '').lower()
                or any(search in t.lower() for t in _parse_json_field(p.technologies))
            ]

        if sort_by == 'title':
            projects.sort(key=lambda p: p.title.lower())
        else:
            projects.sort(key=lambda p: p.level)

        result = [_project_to_dict(p) for p in projects]

    return jsonify({'projects': result, 'total': len(result)}), 200


@projects_bp.route('/<project_id>', methods=['GET'])
def get_project(project_id):
    """Get detailed project information including prerequisite details."""
    with get_db() as db:
        project = db.get(Project, project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404

        # Build prerequisiteDetails from project_prerequisites table
        prereq_rows = (
            db.query(ProjectPrerequisite)
            .filter(ProjectPrerequisite.project_id == project_id)
            .all()
        )
        prereq_details = {'required': [], 'recommended': []}
        for row in prereq_rows:
            if row.kind == 'required':
                prereq_details['required'].append(row.label)
            else:
                prereq_details['recommended'].append(row.label)

        data = _project_to_dict(project)
        data['prerequisiteDetails'] = prereq_details

    return jsonify({'project': data}), 200


@projects_bp.route('/<project_id>/start', methods=['POST'])
@jwt_required()
def start_project(project_id):
    """Start a project for the current user."""
    user_id = get_jwt_identity()

    with get_db() as db:
        user = db.get(User, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        project = db.get(Project, project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404

        # Already started?
        existing_up = (
            db.query(UserProject)
            .filter(UserProject.user_id == user_id, UserProject.project_id == project_id)
            .first()
        )
        if existing_up:
            if existing_up.status == 'completed':
                return jsonify({'message': 'Project already completed'}), 200
            return jsonify({'message': 'Project already started'}), 200

        milestone_ids = _parse_json_field(project.milestone_ids)

        # Create user_project row
        up = UserProject(
            user_id=user_id,
            project_id=project_id,
            started_at=now_iso(),
            progress=0.0,
            status='active',
        )
        db.add(up)
        db.flush()

        # Create user_project_milestone rows: first available, rest locked
        for i, mid in enumerate(milestone_ids):
            status = 'available' if i == 0 else 'locked'
            db.add(UserProjectMilestone(
                user_id=user_id,
                project_id=project_id,
                milestone_id=mid,
                status=status,
            ))

        user.updated_at = now_iso()

        # Return shape matching the old JSON structure
        milestones_dict = {mid: ('available' if i == 0 else 'locked') for i, mid in enumerate(milestone_ids)}
        user_project_payload = {
            'projectId': project_id,
            'startedAt': up.started_at,
            'milestones': milestones_dict,
            'completedMilestones': [],
            'progress': 0,
        }

    return jsonify({'message': 'Project started', 'userProject': user_project_payload}), 201


@projects_bp.route('/recommended', methods=['GET'])
@jwt_required()
def recommended_projects():
    """Get personalized project recommendations based on user profile."""
    user_id = get_jwt_identity()

    with get_db() as db:
        user = db.get(User, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # IDs to exclude
        started_or_done = {
            row.project_id
            for row in db.query(UserProject)
            .filter(UserProject.user_id == user_id)
            .all()
        }
        completed_ids = {
            row.project_id
            for row in db.query(UserProject)
            .filter(UserProject.user_id == user_id, UserProject.status == 'completed')
            .all()
        }

        interested_domains = _parse_json_field(user.interested_domains)
        skill_level = user.skill_level or 'beginner'
        branch = user.branch_id or ''

        skill_map = {
            'beginner': [1, 2, 3],
            'intermediate': [3, 4, 5, 6],
            'advanced': [6, 7, 8, 9, 10],
        }
        level_range = skill_map.get(skill_level, [1, 2, 3])

        all_projects = db.query(Project).all()
        scored = []
        for p in all_projects:
            if p.id in started_or_done:
                continue
            score = 0
            if p.domain_id in interested_domains:
                score += 30
            if branch and branch in _parse_json_field(p.branches):
                score += 20
            if p.level in level_range:
                score += 25
            prereq_ids = _parse_json_field(p.prerequisites)
            if all(pid in completed_ids for pid in prereq_ids):
                score += 25
            elif not prereq_ids:
                score += 15
            scored.append((score, _project_to_dict(p)))

    scored.sort(key=lambda x: x[0], reverse=True)
    recommendations = [d for _, d in scored[:10]]
    return jsonify({'recommendations': recommendations}), 200


@projects_bp.route('/domains', methods=['GET'])
def list_domains():
    """List all available domains."""
    with get_db() as db:
        domains = db.query(Domain).order_by(Domain.name).all()
        result = [_domain_to_dict(d) for d in domains]
    return jsonify({'domains': result}), 200


@projects_bp.route('/branches', methods=['GET'])
def list_branches():
    """List all available academic branches."""
    with get_db() as db:
        branches = db.query(Branch).order_by(Branch.name).all()
        result = [_branch_to_dict(b) for b in branches]
    return jsonify({'branches': result}), 200
