"""
models.py
---------
SQLAlchemy ORM models — one class per database table.

Design notes
------------
* All JSON arrays (technologies, branches, etc.) are stored as plain TEXT
  using json.dumps/loads helpers defined at the bottom of this file.
* Booleans are stored as INTEGER (0/1) — SQLite has no native BOOL type.
* Timestamps are stored as TEXT in ISO-8601 UTC format ("2026-09-22T17:57:33.545751Z").
* The `password` field from users.json is stored as `password_hash` to make
  the intent explicit; the API surface still strips it from every response.
"""
import json
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, Text, Float, ForeignKey, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import relationship

from database import Base


# ── Helpers ───────────────────────────────────────────────────────────────────

def _to_json(value) -> str:
    """Serialise a Python list/dict to a JSON string for TEXT storage."""
    if value is None:
        return "[]"
    if isinstance(value, str):
        return value          # already serialised
    return json.dumps(value, ensure_ascii=False)


def _from_json(value, default=None):
    """Deserialise a TEXT column back to a Python object."""
    if default is None:
        default = []
    if not value:
        return default
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


# ─────────────────────────────────────────────────────────────────────────────
# Reference / catalogue tables
# ─────────────────────────────────────────────────────────────────────────────

class Domain(Base):
    __tablename__ = "domains"

    id          = Column(Text, primary_key=True)   # e.g. "web-development"
    name        = Column(Text, nullable=False, unique=True)
    icon        = Column(Text, nullable=False, default="")
    description = Column(Text, nullable=False, default="")
    color       = Column(Text, nullable=False, default="")

    projects    = relationship("Project", back_populates="domain_rel", lazy="select")

    def to_dict(self):
        return {
            "id":          self.id,
            "name":        self.name,
            "icon":        self.icon,
            "description": self.description,
            "color":       self.color,
            "projectCount": len(self.projects),
        }


class Branch(Base):
    __tablename__ = "branches"

    id         = Column(Text, primary_key=True)   # e.g. "CSE"
    name       = Column(Text, nullable=False, unique=True)
    short_name = Column(Text, nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "shortName": self.short_name}


class Achievement(Base):
    __tablename__ = "achievements"

    id          = Column(Text, primary_key=True)   # e.g. "first-build"
    name        = Column(Text, nullable=False, unique=True)
    description = Column(Text, nullable=False, default="")
    icon        = Column(Text, nullable=False, default="")
    criteria    = Column(Text, nullable=False, default="{}")  # JSON
    xp_reward   = Column(Integer, nullable=False, default=0)

    user_achievements = relationship("UserAchievement", back_populates="achievement", lazy="select")

    def to_dict(self, unlocked: bool = False):
        return {
            "id":          self.id,
            "name":        self.name,
            "description": self.description,
            "icon":        self.icon,
            "criteria":    _from_json(self.criteria, default={}),
            "xpReward":    self.xp_reward,
            "unlocked":    unlocked,
        }


class XpLevel(Base):
    __tablename__ = "xp_levels"

    level  = Column(Integer, primary_key=True)
    name   = Column(Text, nullable=False, unique=True)
    min_xp = Column(Integer, nullable=False)

    def to_dict(self):
        return {"level": self.level, "name": self.name, "minXP": self.min_xp}


class XpActionRule(Base):
    __tablename__ = "xp_action_rules"

    action   = Column(Text, primary_key=True)  # e.g. "complete_learning_milestone"
    xp_value = Column(Integer, nullable=False)

    def to_dict(self):
        return {"action": self.action, "xpValue": self.xp_value}


class MotivationalMessage(Base):
    __tablename__ = "motivational_messages"

    id       = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(Text, nullable=False)   # milestone | project_complete | streak
    message  = Column(Text, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "category IN ('milestone','project_complete','streak')",
            name="chk_msg_category"
        ),
    )

    def to_dict(self):
        return {"id": self.id, "category": self.category, "message": self.message}


# ─────────────────────────────────────────────────────────────────────────────
# Projects
# ─────────────────────────────────────────────────────────────────────────────

class Project(Base):
    __tablename__ = "projects"

    id              = Column(Text, primary_key=True)   # e.g. "web-001"
    domain_id       = Column(Text, ForeignKey("domains.id"), nullable=False)
    title           = Column(Text, nullable=False, unique=True)
    difficulty      = Column(Text, nullable=False)
    level           = Column(Integer, nullable=False)
    type            = Column(Text, nullable=False, default="")
    # JSON arrays stored as TEXT
    branches        = Column(Text, nullable=False, default="[]")
    technologies    = Column(Text, nullable=False, default="[]")
    description     = Column(Text, nullable=False, default="")
    why_build_this  = Column(Text, nullable=False, default="")
    what_you_learn  = Column(Text, nullable=False, default="[]")
    prerequisites   = Column(Text, nullable=False, default="[]")   # list of project IDs
    estimated_hours = Column(Integer, nullable=False, default=0)
    milestone_ids   = Column(Text, nullable=False, default="[]")   # ordered list

    __table_args__ = (
        CheckConstraint(
            "difficulty IN ('beginner','intermediate','advanced')",
            name="chk_project_difficulty"
        ),
        CheckConstraint("level BETWEEN 1 AND 10", name="chk_project_level"),
    )

    domain_rel      = relationship("Domain", back_populates="projects")
    prereq_labels   = relationship(
        "ProjectPrerequisite", back_populates="project",
        cascade="all, delete-orphan", lazy="select"
    )
    milestones      = relationship(
        "Milestone", back_populates="project",
        cascade="all, delete-orphan", lazy="select"
    )

    def to_dict(self, include_prereq_details: bool = False):
        d = {
            "id":             self.id,
            "domain":         self.domain_id,
            "title":          self.title,
            "difficulty":     self.difficulty,
            "level":          self.level,
            "type":           self.type,
            "branches":       _from_json(self.branches),
            "technologies":   _from_json(self.technologies),
            "description":    self.description,
            "whyBuildThis":   self.why_build_this,
            "whatYouLearn":   _from_json(self.what_you_learn),
            "prerequisites":  _from_json(self.prerequisites),
            "estimatedHours": self.estimated_hours,
            "milestoneIds":   _from_json(self.milestone_ids),
        }
        if include_prereq_details:
            required     = [p.label for p in self.prereq_labels if p.kind == "required"]
            recommended  = [p.label for p in self.prereq_labels if p.kind == "recommended"]
            d["prerequisiteDetails"] = {"required": required, "recommended": recommended}
        return d


class ProjectPrerequisite(Base):
    """Text-label prerequisites from prerequisites.json (not project-ID links)."""
    __tablename__ = "project_prerequisites"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Text, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    kind       = Column(Text, nullable=False)   # "required" | "recommended"
    label      = Column(Text, nullable=False)

    __table_args__ = (
        UniqueConstraint("project_id", "kind", "label", name="uq_prereq"),
        CheckConstraint("kind IN ('required','recommended')", name="chk_prereq_kind"),
    )

    project = relationship("Project", back_populates="prereq_labels")


class Milestone(Base):
    """Content for each milestone step (milestones.json — empty initially)."""
    __tablename__ = "milestones"

    id              = Column(Text, primary_key=True)   # e.g. "web-001-m01"
    project_id      = Column(Text, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    title           = Column(Text, nullable=False, default="")
    objective       = Column(Text, nullable=False, default="")
    why             = Column(Text, nullable=False, default="")
    concept         = Column(Text, nullable=False, default="")
    explanation     = Column(Text, nullable=False, default="")
    implementation  = Column(Text, nullable=False, default="")
    expected_result = Column(Text, nullable=False, default="")
    verification    = Column(Text, nullable=False, default="")
    common_errors   = Column(Text, nullable=False, default="[]")  # JSON array
    debugging       = Column(Text, nullable=False, default="")
    sort_order      = Column(Integer, nullable=False, default=0)

    project = relationship("Project", back_populates="milestones")

    def to_dict(self):
        return {
            "id":             self.id,
            "title":          self.title,
            "objective":      self.objective,
            "why":            self.why,
            "concept":        self.concept,
            "explanation":    self.explanation,
            "implementation": self.implementation,
            "expectedResult": self.expected_result,
            "verification":   self.verification,
            "commonErrors":   _from_json(self.common_errors),
            "debugging":      self.debugging,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Users and progress
# ─────────────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id                  = Column(Text, primary_key=True)         # UUID
    name                = Column(Text, nullable=False)
    email               = Column(Text, nullable=False, unique=True)
    password_hash       = Column(Text, nullable=False)
    profile_image       = Column(Text, nullable=False, default="")
    degree              = Column(Text, nullable=False, default="")
    branch_id           = Column(Text, ForeignKey("branches.id"), nullable=True)
    semester            = Column(Text, nullable=False, default="")
    skill_level         = Column(Text, nullable=False, default="beginner")
    interested_domains  = Column(Text, nullable=False, default="[]")  # JSON array
    goals               = Column(Text, nullable=False, default="[]")  # JSON array
    xp                  = Column(Integer, nullable=False, default=0)
    onboarding_complete = Column(Integer, nullable=False, default=0)  # 0/1
    active_days         = Column(Text, nullable=False, default="[]")  # JSON array of dates
    copilot_used        = Column(Integer, nullable=False, default=0)  # 0/1
    created_at          = Column(Text, nullable=False)
    updated_at          = Column(Text, nullable=False)

    branch              = relationship("Branch", lazy="select")
    user_projects       = relationship(
        "UserProject", back_populates="user",
        cascade="all, delete-orphan", lazy="select"
    )
    user_achievements   = relationship(
        "UserAchievement", back_populates="user",
        cascade="all, delete-orphan", lazy="select"
    )
    discussions         = relationship("Discussion", back_populates="user", lazy="select")
    showcases           = relationship("Showcase", back_populates="user", lazy="select")

    def _safe_dict(self):
        """Return public user data — never exposes password_hash."""
        active_projects   = [up for up in self.user_projects if up.status == "active"]
        completed_project_ids = [up.project_id for up in self.user_projects if up.status == "completed"]

        current_projects = []
        for up in active_projects:
            milestones_map = {}
            completed_ms   = []
            for m in up.milestone_statuses:
                milestones_map[m.milestone_id] = m.status
                if m.status == "completed":
                    completed_ms.append(m.milestone_id)
            current_projects.append({
                "projectId":          up.project_id,
                "startedAt":          up.started_at,
                "milestones":         milestones_map,
                "completedMilestones": completed_ms,
                "progress":           up.progress,
            })

        return {
            "id":                 self.id,
            "name":               self.name,
            "email":              self.email,
            "profileImage":       self.profile_image,
            "degree":             self.degree,
            "branch":             self.branch_id or "",
            "semester":           self.semester,
            "skillLevel":         self.skill_level,
            "interestedDomains":  _from_json(self.interested_domains),
            "goals":              _from_json(self.goals),
            "completedProjects":  completed_project_ids,
            "currentProjects":    current_projects,
            "xp":                 self.xp,
            "achievements":       [ua.achievement_id for ua in self.user_achievements],
            "onboardingComplete": bool(self.onboarding_complete),
            "activeDays":         _from_json(self.active_days),
            "copilotUsed":        bool(self.copilot_used),
            "createdAt":          self.created_at,
            "updatedAt":          self.updated_at,
        }


class UserProject(Base):
    """Tracks which projects a user has started or completed."""
    __tablename__ = "user_projects"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(Text, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(Text, ForeignKey("projects.id"), nullable=False)
    started_at = Column(Text, nullable=False)
    progress   = Column(Float, nullable=False, default=0.0)
    status     = Column(Text, nullable=False, default="active")   # active | completed

    __table_args__ = (
        UniqueConstraint("user_id", "project_id", name="uq_user_project"),
        CheckConstraint("status IN ('active','completed')", name="chk_up_status"),
    )

    user              = relationship("User", back_populates="user_projects")
    milestone_statuses = relationship(
        "UserProjectMilestone",
        primaryjoin=(
            "and_(UserProject.user_id == foreign(UserProjectMilestone.user_id), "
            "UserProject.project_id == foreign(UserProjectMilestone.project_id))"
        ),
        viewonly=True,
        lazy="select",
        overlaps="user_project",
    )


class UserProjectMilestone(Base):
    """Per-milestone completion status for a user's project."""
    __tablename__ = "user_project_milestones"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    user_id      = Column(Text, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id   = Column(Text, ForeignKey("projects.id"), nullable=False)
    milestone_id = Column(Text, nullable=False)
    status       = Column(Text, nullable=False, default="locked")

    __table_args__ = (
        UniqueConstraint("user_id", "project_id", "milestone_id", name="uq_upm"),
        CheckConstraint(
            "status IN ('locked','available','completed')",
            name="chk_upm_status"
        ),
    )

    # Read-only link back to the parent UserProject (no real FK exists between
    # user_project_milestones and user_projects; navigation is done explicitly).
    user_project = relationship(
        "UserProject",
        primaryjoin=(
            "and_(foreign(UserProjectMilestone.user_id) == UserProject.user_id, "
            "foreign(UserProjectMilestone.project_id) == UserProject.project_id)"
        ),
        viewonly=True,
        lazy="select",
        overlaps="milestone_statuses",
    )


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    user_id        = Column(Text, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    achievement_id = Column(Text, ForeignKey("achievements.id", ondelete="CASCADE"), primary_key=True)
    unlocked_at    = Column(Text, nullable=False)

    user        = relationship("User", back_populates="user_achievements")
    achievement = relationship("Achievement", back_populates="user_achievements")


# ─────────────────────────────────────────────────────────────────────────────
# Community
# ─────────────────────────────────────────────────────────────────────────────

class Discussion(Base):
    __tablename__ = "discussions"

    id         = Column(Text, primary_key=True)   # UUID
    project_id = Column(Text, ForeignKey("projects.id"), nullable=False)
    user_id    = Column(Text, ForeignKey("users.id"), nullable=False)
    user_name  = Column(Text, nullable=False)
    title      = Column(Text, nullable=False, default="")
    content    = Column(Text, nullable=False)
    parent_id  = Column(Text, ForeignKey("discussions.id"), nullable=True)
    upvotes    = Column(Integer, nullable=False, default=0)
    created_at = Column(Text, nullable=False)

    user    = relationship("User", back_populates="discussions")
    upvoters = relationship(
        "DiscussionUpvote", back_populates="discussion",
        cascade="all, delete-orphan", lazy="select"
    )

    def to_dict(self):
        return {
            "id":         self.id,
            "projectId":  self.project_id,
            "userId":     self.user_id,
            "userName":   self.user_name,
            "title":      self.title,
            "content":    self.content,
            "parentId":   self.parent_id,
            "upvotes":    self.upvotes,
            "upvotedBy":  [u.user_id for u in self.upvoters],
            "createdAt":  self.created_at,
        }


class DiscussionUpvote(Base):
    __tablename__ = "discussion_upvotes"

    discussion_id = Column(Text, ForeignKey("discussions.id", ondelete="CASCADE"), primary_key=True)
    user_id       = Column(Text, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    discussion = relationship("Discussion", back_populates="upvoters")


# ─────────────────────────────────────────────────────────────────────────────
# Showcase
# ─────────────────────────────────────────────────────────────────────────────

class Showcase(Base):
    __tablename__ = "showcases"

    id               = Column(Text, primary_key=True)   # UUID
    user_id          = Column(Text, ForeignKey("users.id"), nullable=False)
    user_name        = Column(Text, nullable=False)
    project_id       = Column(Text, ForeignKey("projects.id"), nullable=False)
    project_name     = Column(Text, nullable=False, default="")
    description      = Column(Text, nullable=False, default="")
    technologies     = Column(Text, nullable=False, default="[]")   # JSON array
    screenshot_url   = Column(Text, nullable=False, default="")
    demo_url         = Column(Text, nullable=False, default="")
    github_url       = Column(Text, nullable=False, default="")
    what_i_learned   = Column(Text, nullable=False, default="")
    challenges_faced = Column(Text, nullable=False, default="")
    created_at       = Column(Text, nullable=False)

    user = relationship("User", back_populates="showcases")

    def to_dict(self):
        return {
            "id":              self.id,
            "userId":          self.user_id,
            "userName":        self.user_name,
            "projectId":       self.project_id,
            "projectName":     self.project_name,
            "description":     self.description,
            "technologies":    _from_json(self.technologies),
            "screenshotUrl":   self.screenshot_url,
            "demoUrl":         self.demo_url,
            "githubUrl":       self.github_url,
            "whatILearned":    self.what_i_learned,
            "challengesFaced": self.challenges_faced,
            "createdAt":       self.created_at,
        }
