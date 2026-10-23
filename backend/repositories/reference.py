"""
repositories/reference.py
--------------------------
CRUD repositories for the reference / catalogue tables:
  Domain, Branch, Achievement, XpLevel, XpActionRule, MotivationalMessage
"""
from typing import Optional

from sqlalchemy.orm import Session

from models import Domain, Branch, Achievement, XpLevel, XpActionRule, MotivationalMessage


# ── Domain ────────────────────────────────────────────────────────────────────

def list_domains(db: Session) -> list[Domain]:
    return db.query(Domain).order_by(Domain.name).all()


def get_domain(db: Session, domain_id: str) -> Optional[Domain]:
    return db.get(Domain, domain_id)


def create_domain(db: Session, id: str, name: str, icon: str = "",
                  description: str = "", color: str = "") -> Domain:
    domain = Domain(id=id, name=name, icon=icon, description=description, color=color)
    db.add(domain)
    db.flush()
    return domain


def update_domain(db: Session, domain_id: str, **kwargs) -> Optional[Domain]:
    domain = db.get(Domain, domain_id)
    if not domain:
        return None
    allowed = {"name", "icon", "description", "color"}
    for key, value in kwargs.items():
        if key in allowed:
            setattr(domain, key, value)
    db.flush()
    return domain


def delete_domain(db: Session, domain_id: str) -> bool:
    domain = db.get(Domain, domain_id)
    if not domain:
        return False
    db.delete(domain)
    db.flush()
    return True


# ── Branch ────────────────────────────────────────────────────────────────────

def list_branches(db: Session) -> list[Branch]:
    return db.query(Branch).order_by(Branch.name).all()


def get_branch(db: Session, branch_id: str) -> Optional[Branch]:
    return db.get(Branch, branch_id)


def create_branch(db: Session, id: str, name: str, short_name: str) -> Branch:
    branch = Branch(id=id, name=name, short_name=short_name)
    db.add(branch)
    db.flush()
    return branch


def update_branch(db: Session, branch_id: str, **kwargs) -> Optional[Branch]:
    branch = db.get(Branch, branch_id)
    if not branch:
        return None
    for key, value in kwargs.items():
        if key in {"name", "short_name"}:
            setattr(branch, key, value)
    db.flush()
    return branch


def delete_branch(db: Session, branch_id: str) -> bool:
    branch = db.get(Branch, branch_id)
    if not branch:
        return False
    db.delete(branch)
    db.flush()
    return True


# ── Achievement ───────────────────────────────────────────────────────────────

def list_achievements(db: Session) -> list[Achievement]:
    return db.query(Achievement).order_by(Achievement.name).all()


def get_achievement(db: Session, achievement_id: str) -> Optional[Achievement]:
    return db.get(Achievement, achievement_id)


def create_achievement(db: Session, id: str, name: str, description: str = "",
                       icon: str = "", criteria: str = "{}", xp_reward: int = 0) -> Achievement:
    ach = Achievement(id=id, name=name, description=description,
                      icon=icon, criteria=criteria, xp_reward=xp_reward)
    db.add(ach)
    db.flush()
    return ach


def update_achievement(db: Session, achievement_id: str, **kwargs) -> Optional[Achievement]:
    ach = db.get(Achievement, achievement_id)
    if not ach:
        return None
    for key, value in kwargs.items():
        if key in {"name", "description", "icon", "criteria", "xp_reward"}:
            setattr(ach, key, value)
    db.flush()
    return ach


def delete_achievement(db: Session, achievement_id: str) -> bool:
    ach = db.get(Achievement, achievement_id)
    if not ach:
        return False
    db.delete(ach)
    db.flush()
    return True


# ── XpLevel ───────────────────────────────────────────────────────────────────

def list_xp_levels(db: Session) -> list[XpLevel]:
    return db.query(XpLevel).order_by(XpLevel.level).all()


def get_xp_level(db: Session, level: int) -> Optional[XpLevel]:
    return db.get(XpLevel, level)


def create_xp_level(db: Session, level: int, name: str, min_xp: int) -> XpLevel:
    xp_level = XpLevel(level=level, name=name, min_xp=min_xp)
    db.add(xp_level)
    db.flush()
    return xp_level


def update_xp_level(db: Session, level: int, **kwargs) -> Optional[XpLevel]:
    xp_level = db.get(XpLevel, level)
    if not xp_level:
        return None
    for key, value in kwargs.items():
        if key in {"name", "min_xp"}:
            setattr(xp_level, key, value)
    db.flush()
    return xp_level


def delete_xp_level(db: Session, level: int) -> bool:
    xp_level = db.get(XpLevel, level)
    if not xp_level:
        return False
    db.delete(xp_level)
    db.flush()
    return True


# ── XpActionRule ──────────────────────────────────────────────────────────────

def list_xp_action_rules(db: Session) -> list[XpActionRule]:
    return db.query(XpActionRule).order_by(XpActionRule.action).all()


def get_xp_action_rule(db: Session, action: str) -> Optional[XpActionRule]:
    return db.get(XpActionRule, action)


def create_xp_action_rule(db: Session, action: str, xp_value: int) -> XpActionRule:
    rule = XpActionRule(action=action, xp_value=xp_value)
    db.add(rule)
    db.flush()
    return rule


def update_xp_action_rule(db: Session, action: str, xp_value: int) -> Optional[XpActionRule]:
    rule = db.get(XpActionRule, action)
    if not rule:
        return None
    rule.xp_value = xp_value
    db.flush()
    return rule


def delete_xp_action_rule(db: Session, action: str) -> bool:
    rule = db.get(XpActionRule, action)
    if not rule:
        return False
    db.delete(rule)
    db.flush()
    return True


# ── MotivationalMessage ───────────────────────────────────────────────────────

def list_motivational_messages(db: Session, category: Optional[str] = None
                               ) -> list[MotivationalMessage]:
    q = db.query(MotivationalMessage)
    if category:
        q = q.filter(MotivationalMessage.category == category)
    return q.order_by(MotivationalMessage.id).all()


def get_motivational_message(db: Session, message_id: int) -> Optional[MotivationalMessage]:
    return db.get(MotivationalMessage, message_id)


def create_motivational_message(db: Session, category: str, message: str) -> MotivationalMessage:
    msg = MotivationalMessage(category=category, message=message)
    db.add(msg)
    db.flush()
    return msg


def update_motivational_message(db: Session, message_id: int, **kwargs) -> Optional[MotivationalMessage]:
    msg = db.get(MotivationalMessage, message_id)
    if not msg:
        return None
    for key, value in kwargs.items():
        if key in {"category", "message"}:
            setattr(msg, key, value)
    db.flush()
    return msg


def delete_motivational_message(db: Session, message_id: int) -> bool:
    msg = db.get(MotivationalMessage, message_id)
    if not msg:
        return False
    db.delete(msg)
    db.flush()
    return True
