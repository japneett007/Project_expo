"""
seed.py
-------
Idempotent database seeder.

Reads every JSON file from data/ and inserts the records into the
corresponding SQLAlchemy tables.  Safe to run multiple times:
  - Records whose PK already exists are skipped (no duplicate rows).
  - Source files in data/ are never modified or deleted.

Usage:
    cd backend
    python seed.py
"""
import json
import os
import sys

# Make sure we can import database / models from the backend directory
sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal, engine      # noqa: E402
import models                                  # noqa: E402  registers all ORM classes
from database import Base                      # noqa: E402

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))


def _load(filename):
    """Read a JSON file from data/ and return the parsed object."""
    path = os.path.join(DATA_DIR, filename)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _upsert_or_skip(db, model_cls, pk_field, record, transform=None):
    """Insert record only if its PK is not already in the table."""
    data = transform(record) if transform else record
    pk_value = data[pk_field]
    existing = db.get(model_cls, pk_value)
    if existing is not None:
        return 'skipped', existing
    obj = model_cls(**data)
    db.add(obj)
    return 'inserted', obj


# ── Seed functions ────────────────────────────────────────────────────────────

def seed_branches(db):
    rows = _load('branches.json')
    counts = {'inserted': 0, 'skipped': 0}
    for r in rows:
        action, _ = _upsert_or_skip(db, models.Branch, 'id', r, lambda x: {
            'id':         x['id'],
            'name':       x['name'],
            'short_name': x.get('shortName', x.get('short_name', x['id'])),
        })
        counts[action] += 1
    db.flush()
    return counts


def seed_domains(db):
    rows = _load('domains.json')
    counts = {'inserted': 0, 'skipped': 0}
    for r in rows:
        action, _ = _upsert_or_skip(db, models.Domain, 'id', r, lambda x: {
            'id':          x['id'],
            'name':        x['name'],
            'icon':        x.get('icon', ''),
            'description': x.get('description', ''),
            'color':       x.get('color', ''),
        })
        counts[action] += 1
    db.flush()
    return counts


def seed_achievements(db):
    rows = _load('achievements.json')
    counts = {'inserted': 0, 'skipped': 0}
    for r in rows:
        action, _ = _upsert_or_skip(db, models.Achievement, 'id', r, lambda x: {
            'id':          x['id'],
            'name':        x['name'],
            'description': x.get('description', ''),
            'icon':        x.get('icon', ''),
            'criteria':    json.dumps(x.get('criteria', {}), ensure_ascii=False),
            'xp_reward':   x.get('xpReward', x.get('xp_reward', 0)),
        })
        counts[action] += 1
    db.flush()
    return counts


def seed_xp_rules(db):
    data = _load('xp_rules.json')
    action_counts = {'inserted': 0, 'skipped': 0}
    level_counts  = {'inserted': 0, 'skipped': 0}

    for action, xp_value in data.items():
        if action == 'levels':
            continue
        existing = db.get(models.XpActionRule, action)
        if existing:
            action_counts['skipped'] += 1
            continue
        db.add(models.XpActionRule(action=action, xp_value=int(xp_value)))
        action_counts['inserted'] += 1

    for lvl in data.get('levels', []):
        existing = db.get(models.XpLevel, lvl['level'])
        if existing:
            level_counts['skipped'] += 1
            continue
        db.add(models.XpLevel(
            level=lvl['level'],
            name=lvl['name'],
            min_xp=lvl['minXP'],
        ))
        level_counts['inserted'] += 1

    db.flush()
    return {'xp_action_rules': action_counts, 'xp_levels': level_counts}


def seed_motivational_messages(db):
    data = _load('motivational_messages.json')
    category_map = {
        'milestone_messages':        'milestone',
        'project_complete_messages': 'project_complete',
        'streak_messages':           'streak',
    }
    counts = {'inserted': 0, 'skipped': 0}
    for key, messages in data.items():
        category = category_map.get(key)
        if not category:
            continue
        for msg_text in messages:
            existing = db.query(models.MotivationalMessage).filter_by(
                category=category, message=msg_text
            ).first()
            if existing:
                counts['skipped'] += 1
                continue
            db.add(models.MotivationalMessage(category=category, message=msg_text))
            counts['inserted'] += 1
    db.flush()
    return counts


def seed_projects(db):
    rows = _load('projects.json')
    counts = {'inserted': 0, 'skipped': 0}
    for r in rows:
        action, _ = _upsert_or_skip(db, models.Project, 'id', r, lambda x: {
            'id':              x['id'],
            'domain_id':       x.get('domain', x.get('domain_id', '')),
            'title':           x['title'],
            'difficulty':      x['difficulty'],
            'level':           x['level'],
            'type':            x.get('type', ''),
            'branches':        json.dumps(x.get('branches', []), ensure_ascii=False),
            'technologies':    json.dumps(x.get('technologies', []), ensure_ascii=False),
            'description':     x.get('description', ''),
            'why_build_this':  x.get('whyBuildThis', x.get('why_build_this', '')),
            'what_you_learn':  json.dumps(x.get('whatYouLearn', x.get('what_you_learn', [])), ensure_ascii=False),
            'prerequisites':   json.dumps(x.get('prerequisites', []), ensure_ascii=False),
            'estimated_hours': x.get('estimatedHours', x.get('estimated_hours', 0)),
            'milestone_ids':   json.dumps(x.get('milestoneIds', x.get('milestone_ids', [])), ensure_ascii=False),
        })
        counts[action] += 1
    db.flush()
    return counts


def seed_prerequisites(db):
    data = _load('prerequisites.json')
    counts = {'inserted': 0, 'skipped': 0}
    for project_id, detail in data.items():
        for kind in ('required', 'recommended'):
            for label in detail.get(kind, []):
                existing = db.query(models.ProjectPrerequisite).filter_by(
                    project_id=project_id, kind=kind, label=label
                ).first()
                if existing:
                    counts['skipped'] += 1
                    continue
                db.add(models.ProjectPrerequisite(
                    project_id=project_id,
                    kind=kind,
                    label=label,
                ))
                counts['inserted'] += 1
    db.flush()
    return counts


def seed_milestones(db):
    rows = _load('milestones.json')
    if not rows:
        return {'inserted': 0, 'skipped': 0}
    counts = {'inserted': 0, 'skipped': 0}
    for r in rows:
        action, _ = _upsert_or_skip(db, models.Milestone, 'id', r, lambda x: {
            'id':              x['id'],
            'project_id':      x['project_id'],
            'title':           x.get('title', ''),
            'objective':       x.get('objective', ''),
            'why':             x.get('why', ''),
            'concept':         x.get('concept', ''),
            'explanation':     x.get('explanation', ''),
            'implementation':  x.get('implementation', ''),
            'expected_result': x.get('expectedResult', x.get('expected_result', '')),
            'verification':    x.get('verification', ''),
            'common_errors':   json.dumps(x.get('commonErrors', x.get('common_errors', [])), ensure_ascii=False),
            'debugging':       x.get('debugging', ''),
            'sort_order':      x.get('sort_order', 0),
        })
        counts[action] += 1
    db.flush()
    return counts


def seed_users(db):
    rows = _load('users.json')
    counts = {'inserted': 0, 'skipped': 0}
    for r in rows:
        action, _ = _upsert_or_skip(db, models.User, 'id', r, lambda x: {
            'id':                  x['id'],
            'name':                x['name'],
            'email':               x['email'],
            'password_hash':       x.get('password', x.get('password_hash', '')),
            'profile_image':       x.get('profileImage', x.get('profile_image', '')),
            'degree':              x.get('degree', ''),
            'branch_id':           x.get('branch', x.get('branch_id')) or None,
            'semester':            x.get('semester', ''),
            'skill_level':         x.get('skillLevel', x.get('skill_level', 'beginner')),
            'interested_domains':  json.dumps(x.get('interestedDomains', x.get('interested_domains', [])), ensure_ascii=False),
            'goals':               json.dumps(x.get('goals', []), ensure_ascii=False),
            'xp':                  x.get('xp', 0),
            'onboarding_complete': int(x.get('onboardingComplete', x.get('onboarding_complete', False))),
            'active_days':         json.dumps(x.get('activeDays', x.get('active_days', [])), ensure_ascii=False),
            'copilot_used':        int(x.get('copilotUsed', x.get('copilot_used', False))),
            'created_at':          x.get('createdAt', x.get('created_at', '')),
            'updated_at':          x.get('updatedAt', x.get('updated_at', '')),
        })
        counts[action] += 1
    db.flush()

    up_counts  = {'inserted': 0, 'skipped': 0}
    upm_counts = {'inserted': 0, 'skipped': 0}
    ua_counts  = {'inserted': 0, 'skipped': 0}

    from datetime import datetime, timezone
    _now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

    for r in rows:
        user_id = r['id']

        for proj_id in r.get('completedProjects', []):
            existing = db.query(models.UserProject).filter_by(
                user_id=user_id, project_id=proj_id
            ).first()
            if existing:
                up_counts['skipped'] += 1
            else:
                db.add(models.UserProject(
                    user_id=user_id,
                    project_id=proj_id,
                    started_at=_now,
                    progress=100.0,
                    status='completed',
                ))
                up_counts['inserted'] += 1

        for cp in r.get('currentProjects', []):
            proj_id = cp['projectId']
            existing = db.query(models.UserProject).filter_by(
                user_id=user_id, project_id=proj_id
            ).first()
            if existing:
                up_counts['skipped'] += 1
            else:
                db.add(models.UserProject(
                    user_id=user_id,
                    project_id=proj_id,
                    started_at=cp.get('startedAt', _now),
                    progress=float(cp.get('progress', 0)),
                    status='active',
                ))
                up_counts['inserted'] += 1

            for m_id, m_status in cp.get('milestones', {}).items():
                existing = db.query(models.UserProjectMilestone).filter_by(
                    user_id=user_id, project_id=proj_id, milestone_id=m_id
                ).first()
                if existing:
                    upm_counts['skipped'] += 1
                else:
                    db.add(models.UserProjectMilestone(
                        user_id=user_id,
                        project_id=proj_id,
                        milestone_id=m_id,
                        status=m_status,
                    ))
                    upm_counts['inserted'] += 1

        for ach_id in r.get('achievements', []):
            existing = db.get(models.UserAchievement, (user_id, ach_id))
            if existing:
                ua_counts['skipped'] += 1
            else:
                db.add(models.UserAchievement(
                    user_id=user_id,
                    achievement_id=ach_id,
                    unlocked_at=_now,
                ))
                ua_counts['inserted'] += 1

    db.flush()
    return {
        'users':                   counts,
        'user_projects':           up_counts,
        'user_project_milestones': upm_counts,
        'user_achievements':       ua_counts,
    }


def seed_discussions(db):
    rows = _load('discussions.json')
    if not rows:
        return {'inserted': 0, 'skipped': 0}
    counts = {'inserted': 0, 'skipped': 0}
    for r in rows:
        action, _ = _upsert_or_skip(db, models.Discussion, 'id', r, lambda x: {
            'id':         x['id'],
            'project_id': x.get('projectId', x.get('project_id', '')),
            'user_id':    x.get('userId', x.get('user_id', '')),
            'user_name':  x.get('userName', x.get('user_name', '')),
            'title':      x.get('title', ''),
            'content':    x.get('content', ''),
            'parent_id':  x.get('parentId', x.get('parent_id')),
            'upvotes':    x.get('upvotes', 0),
            'created_at': x.get('createdAt', x.get('created_at', '')),
        })
        counts[action] += 1
        for voter_id in r.get('upvotedBy', []):
            existing = db.get(models.DiscussionUpvote, (r['id'], voter_id))
            if not existing:
                db.add(models.DiscussionUpvote(discussion_id=r['id'], user_id=voter_id))
    db.flush()
    return counts


def seed_showcases(db):
    rows = _load('showcases.json')
    if not rows:
        return {'inserted': 0, 'skipped': 0}
    counts = {'inserted': 0, 'skipped': 0}
    for r in rows:
        action, _ = _upsert_or_skip(db, models.Showcase, 'id', r, lambda x: {
            'id':               x['id'],
            'user_id':          x.get('userId', x.get('user_id', '')),
            'user_name':        x.get('userName', x.get('user_name', '')),
            'project_id':       x.get('projectId', x.get('project_id', '')),
            'project_name':     x.get('projectName', x.get('project_name', '')),
            'description':      x.get('description', ''),
            'technologies':     json.dumps(x.get('technologies', []), ensure_ascii=False),
            'screenshot_url':   x.get('screenshotUrl', x.get('screenshot_url', '')),
            'demo_url':         x.get('demoUrl', x.get('demo_url', '')),
            'github_url':       x.get('githubUrl', x.get('github_url', '')),
            'what_i_learned':   x.get('whatILearned', x.get('what_i_learned', '')),
            'challenges_faced': x.get('challengesFaced', x.get('challenges_faced', '')),
            'created_at':       x.get('createdAt', x.get('created_at', '')),
        })
        counts[action] += 1
    db.flush()
    return counts


# ── Main ──────────────────────────────────────────────────────────────────────

def run_seed():
    db = SessionLocal()
    try:
        print("-" * 60)
        print("Seeding database...")
        print("-" * 60)

        results = {}
        results['branches']               = seed_branches(db)
        results['domains']                = seed_domains(db)
        results['achievements']           = seed_achievements(db)
        xp                               = seed_xp_rules(db)
        results['xp_action_rules']        = xp['xp_action_rules']
        results['xp_levels']              = xp['xp_levels']
        results['motivational_messages']  = seed_motivational_messages(db)
        results['projects']               = seed_projects(db)
        results['project_prerequisites']  = seed_prerequisites(db)
        results['milestones']             = seed_milestones(db)
        user_results                      = seed_users(db)
        results['users']                  = user_results['users']
        results['user_projects']          = user_results['user_projects']
        results['user_project_milestones']= user_results['user_project_milestones']
        results['user_achievements']      = user_results['user_achievements']
        results['discussions']            = seed_discussions(db)
        results['showcases']              = seed_showcases(db)

        db.commit()
        print()
        print(f"{'Table':<32} {'Inserted':>10} {'Skipped':>10}")
        print("-" * 54)
        for table, counts in results.items():
            if isinstance(counts, dict) and 'inserted' in counts:
                print(f"{table:<32} {counts['inserted']:>10} {counts['skipped']:>10}")
        print("-" * 60)
        print("Done.")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == '__main__':
    run_seed()
