"""
repositories/projects.py
-------------------------
CRUD repositories for Project, ProjectPrerequisite, and Milestone.
"""
import json
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import or_

from models import Project, ProjectPrerequisite, Milestone


# ── Project ───────────────────────────────────────────────────────────────────

def list_projects(
    db: Session,
    domain: Optional[str] = None,
    difficulty: Optional[str] = None,
    branch: Optional[str] = None,
    project_type: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "level",
) -> list[Project]:
    q = db.query(Project)
    if domain:
        q = q.filter(Project.domain_id == domain)
    if difficulty:
        q = q.filter(Project.difficulty == difficulty)
    # branch / search must be post-filtered (stored as JSON text)
    projects = q.all()
    if branch:
        projects = [p for p in projects if branch in json.loads(p.branches)]
    if project_type:
        projects = [p for p in projects if p.type.lower() == project_type.lower()]
    if search:
        s = search.lower()
        projects = [
            p for p in projects
            if s in p.title.lower()
            or s in p.description.lower()
            or any(s in t.lower() for t in json.loads(p.technologies))
        ]
    if sort_by == "level":
        projects.sort(key=lambda p: p.level)
    elif sort_by == "title":
        projects.sort(key=lambda p: p.title.lower())
    return projects


def get_project(db: Session, project_id: str) -> Optional[Project]:
    return db.get(Project, project_id)


def create_project(db: Session, **kwargs) -> Project:
    """Create a project. JSON-list fields (branches, technologies, etc.)
    should be passed as Python lists; they are serialised automatically."""
    for list_field in ("branches", "technologies", "what_you_learn",
                       "prerequisites", "milestone_ids"):
        if list_field in kwargs and isinstance(kwargs[list_field], list):
            kwargs[list_field] = json.dumps(kwargs[list_field], ensure_ascii=False)
    project = Project(**kwargs)
    db.add(project)
    db.flush()
    return project


def update_project(db: Session, project_id: str, **kwargs) -> Optional[Project]:
    project = db.get(Project, project_id)
    if not project:
        return None
    allowed = {
        "domain_id", "title", "difficulty", "level", "type",
        "branches", "technologies", "description", "why_build_this",
        "what_you_learn", "prerequisites", "estimated_hours", "milestone_ids",
    }
    for key, value in kwargs.items():
        if key in allowed:
            if isinstance(value, list):
                value = json.dumps(value, ensure_ascii=False)
            setattr(project, key, value)
    db.flush()
    return project


def delete_project(db: Session, project_id: str) -> bool:
    project = db.get(Project, project_id)
    if not project:
        return False
    db.delete(project)
    db.flush()
    return True


# ── ProjectPrerequisite ───────────────────────────────────────────────────────

def list_prereqs(db: Session, project_id: str) -> list[ProjectPrerequisite]:
    return (db.query(ProjectPrerequisite)
              .filter(ProjectPrerequisite.project_id == project_id)
              .order_by(ProjectPrerequisite.kind, ProjectPrerequisite.label)
              .all())


def get_prereq(db: Session, prereq_id: int) -> Optional[ProjectPrerequisite]:
    return db.get(ProjectPrerequisite, prereq_id)


def create_prereq(db: Session, project_id: str, kind: str, label: str) -> ProjectPrerequisite:
    prereq = ProjectPrerequisite(project_id=project_id, kind=kind, label=label)
    db.add(prereq)
    db.flush()
    return prereq


def delete_prereq(db: Session, prereq_id: int) -> bool:
    prereq = db.get(ProjectPrerequisite, prereq_id)
    if not prereq:
        return False
    db.delete(prereq)
    db.flush()
    return True


# ── Milestone ─────────────────────────────────────────────────────────────────

def list_milestones(db: Session, project_id: str) -> list[Milestone]:
    return (db.query(Milestone)
              .filter(Milestone.project_id == project_id)
              .order_by(Milestone.sort_order)
              .all())


def get_milestone(db: Session, milestone_id: str) -> Optional[Milestone]:
    return db.get(Milestone, milestone_id)


def create_milestone(db: Session, **kwargs) -> Milestone:
    if "common_errors" in kwargs and isinstance(kwargs["common_errors"], list):
        kwargs["common_errors"] = json.dumps(kwargs["common_errors"], ensure_ascii=False)
    milestone = Milestone(**kwargs)
    db.add(milestone)
    db.flush()
    return milestone


def update_milestone(db: Session, milestone_id: str, **kwargs) -> Optional[Milestone]:
    milestone = db.get(Milestone, milestone_id)
    if not milestone:
        return None
    allowed = {
        "title", "objective", "why", "concept", "explanation",
        "implementation", "expected_result", "verification",
        "common_errors", "debugging", "sort_order",
    }
    for key, value in kwargs.items():
        if key in allowed:
            if key == "common_errors" and isinstance(value, list):
                value = json.dumps(value, ensure_ascii=False)
            setattr(milestone, key, value)
    db.flush()
    return milestone


def delete_milestone(db: Session, milestone_id: str) -> bool:
    milestone = db.get(Milestone, milestone_id)
    if not milestone:
        return False
    db.delete(milestone)
    db.flush()
    return True
