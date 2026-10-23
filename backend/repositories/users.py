"""
repositories/users.py
----------------------
CRUD repositories for User, UserProject, UserProjectMilestone, UserAchievement.
"""
import json
from typing import Optional

from sqlalchemy.orm import Session

from models import User, UserProject, UserProjectMilestone, UserAchievement


# ── User ──────────────────────────────────────────────────────────────────────

def list_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.name).all()


def get_user(db: Session, user_id: str) -> Optional[User]:
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email.lower()).first()


def create_user(db: Session, **kwargs) -> User:
    for list_field in ("interested_domains", "goals", "active_days"):
        if list_field in kwargs and isinstance(kwargs[list_field], list):
            kwargs[list_field] = json.dumps(kwargs[list_field], ensure_ascii=False)
    if "onboarding_complete" in kwargs and isinstance(kwargs["onboarding_complete"], bool):
        kwargs["onboarding_complete"] = int(kwargs["onboarding_complete"])
    if "copilot_used" in kwargs and isinstance(kwargs["copilot_used"], bool):
        kwargs["copilot_used"] = int(kwargs["copilot_used"])
    user = User(**kwargs)
    db.add(user)
    db.flush()
    return user


def update_user(db: Session, user_id: str, **kwargs) -> Optional[User]:
    user = db.get(User, user_id)
    if not user:
        return None
    allowed = {
        "name", "email", "password_hash", "profile_image", "degree",
        "branch_id", "semester", "skill_level", "interested_domains",
        "goals", "xp", "onboarding_complete", "active_days",
        "copilot_used", "updated_at",
    }
    for key, value in kwargs.items():
        if key in allowed:
            if key in ("interested_domains", "goals", "active_days") and isinstance(value, list):
                value = json.dumps(value, ensure_ascii=False)
            elif key in ("onboarding_complete", "copilot_used") and isinstance(value, bool):
                value = int(value)
            setattr(user, key, value)
    db.flush()
    return user


def delete_user(db: Session, user_id: str) -> bool:
    user = db.get(User, user_id)
    if not user:
        return False
    db.delete(user)
    db.flush()
    return True


# ── UserProject ───────────────────────────────────────────────────────────────

def list_user_projects(db: Session, user_id: str,
                       status: Optional[str] = None) -> list[UserProject]:
    q = db.query(UserProject).filter(UserProject.user_id == user_id)
    if status:
        q = q.filter(UserProject.status == status)
    return q.all()


def get_user_project(db: Session, user_id: str, project_id: str) -> Optional[UserProject]:
    return (db.query(UserProject)
              .filter(UserProject.user_id == user_id,
                      UserProject.project_id == project_id)
              .first())


def create_user_project(db: Session, user_id: str, project_id: str,
                        started_at: str, progress: float = 0.0,
                        status: str = "active") -> UserProject:
    up = UserProject(
        user_id=user_id,
        project_id=project_id,
        started_at=started_at,
        progress=progress,
        status=status,
    )
    db.add(up)
    db.flush()
    return up


def update_user_project(db: Session, user_id: str, project_id: str,
                        **kwargs) -> Optional[UserProject]:
    up = get_user_project(db, user_id, project_id)
    if not up:
        return None
    for key, value in kwargs.items():
        if key in {"progress", "status", "started_at"}:
            setattr(up, key, value)
    db.flush()
    return up


def delete_user_project(db: Session, user_id: str, project_id: str) -> bool:
    up = get_user_project(db, user_id, project_id)
    if not up:
        return False
    db.delete(up)
    db.flush()
    return True


# ── UserProjectMilestone ──────────────────────────────────────────────────────

def list_user_project_milestones(db: Session, user_id: str,
                                 project_id: str) -> list[UserProjectMilestone]:
    return (db.query(UserProjectMilestone)
              .filter(UserProjectMilestone.user_id == user_id,
                      UserProjectMilestone.project_id == project_id)
              .all())


def get_user_project_milestone(db: Session, user_id: str, project_id: str,
                               milestone_id: str) -> Optional[UserProjectMilestone]:
    return (db.query(UserProjectMilestone)
              .filter(UserProjectMilestone.user_id == user_id,
                      UserProjectMilestone.project_id == project_id,
                      UserProjectMilestone.milestone_id == milestone_id)
              .first())


def create_user_project_milestone(db: Session, user_id: str, project_id: str,
                                  milestone_id: str,
                                  status: str = "locked") -> UserProjectMilestone:
    upm = UserProjectMilestone(
        user_id=user_id,
        project_id=project_id,
        milestone_id=milestone_id,
        status=status,
    )
    db.add(upm)
    db.flush()
    return upm


def update_user_project_milestone(db: Session, user_id: str, project_id: str,
                                  milestone_id: str,
                                  status: str) -> Optional[UserProjectMilestone]:
    upm = get_user_project_milestone(db, user_id, project_id, milestone_id)
    if not upm:
        return None
    upm.status = status
    db.flush()
    return upm


def delete_user_project_milestone(db: Session, user_id: str, project_id: str,
                                  milestone_id: str) -> bool:
    upm = get_user_project_milestone(db, user_id, project_id, milestone_id)
    if not upm:
        return False
    db.delete(upm)
    db.flush()
    return True


# ── UserAchievement ───────────────────────────────────────────────────────────

def list_user_achievements(db: Session, user_id: str) -> list[UserAchievement]:
    return (db.query(UserAchievement)
              .filter(UserAchievement.user_id == user_id)
              .all())


def get_user_achievement(db: Session, user_id: str,
                         achievement_id: str) -> Optional[UserAchievement]:
    return db.get(UserAchievement, (user_id, achievement_id))


def create_user_achievement(db: Session, user_id: str, achievement_id: str,
                            unlocked_at: str) -> UserAchievement:
    ua = UserAchievement(
        user_id=user_id,
        achievement_id=achievement_id,
        unlocked_at=unlocked_at,
    )
    db.add(ua)
    db.flush()
    return ua


def delete_user_achievement(db: Session, user_id: str, achievement_id: str) -> bool:
    ua = db.get(UserAchievement, (user_id, achievement_id))
    if not ua:
        return False
    db.delete(ua)
    db.flush()
    return True
