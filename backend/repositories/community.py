"""
repositories/community.py
--------------------------
CRUD repositories for Discussion, DiscussionUpvote, and Showcase.
"""
import json
from typing import Optional

from sqlalchemy.orm import Session

from models import Discussion, DiscussionUpvote, Showcase


# ── Discussion ────────────────────────────────────────────────────────────────

def list_discussions(db: Session, project_id: Optional[str] = None,
                     parent_id: Optional[str] = None) -> list[Discussion]:
    q = db.query(Discussion)
    if project_id:
        q = q.filter(Discussion.project_id == project_id)
    if parent_id is not None:
        q = q.filter(Discussion.parent_id == parent_id)
    return q.order_by(Discussion.created_at.desc()).all()


def get_discussion(db: Session, discussion_id: str) -> Optional[Discussion]:
    return db.get(Discussion, discussion_id)


def create_discussion(db: Session, id: str, project_id: str, user_id: str,
                      user_name: str, content: str, created_at: str,
                      title: str = "", parent_id: Optional[str] = None,
                      upvotes: int = 0) -> Discussion:
    disc = Discussion(
        id=id,
        project_id=project_id,
        user_id=user_id,
        user_name=user_name,
        title=title,
        content=content,
        parent_id=parent_id,
        upvotes=upvotes,
        created_at=created_at,
    )
    db.add(disc)
    db.flush()
    return disc


def update_discussion(db: Session, discussion_id: str, **kwargs) -> Optional[Discussion]:
    disc = db.get(Discussion, discussion_id)
    if not disc:
        return None
    for key, value in kwargs.items():
        if key in {"title", "content", "upvotes"}:
            setattr(disc, key, value)
    db.flush()
    return disc


def delete_discussion(db: Session, discussion_id: str) -> bool:
    disc = db.get(Discussion, discussion_id)
    if not disc:
        return False
    db.delete(disc)
    db.flush()
    return True


# ── DiscussionUpvote ──────────────────────────────────────────────────────────

def get_upvote(db: Session, discussion_id: str, user_id: str) -> Optional[DiscussionUpvote]:
    return db.get(DiscussionUpvote, (discussion_id, user_id))


def add_upvote(db: Session, discussion_id: str, user_id: str) -> DiscussionUpvote:
    upvote = DiscussionUpvote(discussion_id=discussion_id, user_id=user_id)
    db.add(upvote)
    db.flush()
    return upvote


def remove_upvote(db: Session, discussion_id: str, user_id: str) -> bool:
    upvote = db.get(DiscussionUpvote, (discussion_id, user_id))
    if not upvote:
        return False
    db.delete(upvote)
    db.flush()
    return True


# ── Showcase ──────────────────────────────────────────────────────────────────

def list_showcases(db: Session, user_id: Optional[str] = None) -> list[Showcase]:
    q = db.query(Showcase)
    if user_id:
        q = q.filter(Showcase.user_id == user_id)
    return q.order_by(Showcase.created_at.desc()).all()


def get_showcase(db: Session, showcase_id: str) -> Optional[Showcase]:
    return db.get(Showcase, showcase_id)


def create_showcase(db: Session, **kwargs) -> Showcase:
    if "technologies" in kwargs and isinstance(kwargs["technologies"], list):
        kwargs["technologies"] = json.dumps(kwargs["technologies"], ensure_ascii=False)
    showcase = Showcase(**kwargs)
    db.add(showcase)
    db.flush()
    return showcase


def update_showcase(db: Session, showcase_id: str, **kwargs) -> Optional[Showcase]:
    showcase = db.get(Showcase, showcase_id)
    if not showcase:
        return None
    allowed = {
        "project_name", "description", "technologies", "screenshot_url",
        "demo_url", "github_url", "what_i_learned", "challenges_faced",
    }
    for key, value in kwargs.items():
        if key in allowed:
            if key == "technologies" and isinstance(value, list):
                value = json.dumps(value, ensure_ascii=False)
            setattr(showcase, key, value)
    db.flush()
    return showcase


def delete_showcase(db: Session, showcase_id: str) -> bool:
    showcase = db.get(Showcase, showcase_id)
    if not showcase:
        return False
    db.delete(showcase)
    db.flush()
    return True
