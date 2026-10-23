"""
test_db.py
----------
Tests for:
  1. Seed counts vs JSON source counts.
  2. One full create / read / update / delete cycle for every repository.

Run with:
    cd backend
    python test_db.py
"""
import io
import json
import os
import sys
import uuid
import traceback

# Force UTF-8 output on Windows to avoid cp1252 encoding errors
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal, engine, Base
import models  # noqa: registers all ORM classes
import repositories.reference as ref_repo
import repositories.projects  as prj_repo
import repositories.users     as usr_repo
import repositories.community as com_repo

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))

# ── Helpers ───────────────────────────────────────────────────────────────────

PASS = "PASS"
FAIL = "FAIL"
results = []


def check(label: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    results.append((status, label, detail))
    marker = "✓" if condition else "✗"
    print(f"  {marker} {label}" + (f"  [{detail}]" if detail else ""))


def load_json(filename):
    with open(os.path.join(DATA_DIR, filename), encoding='utf-8') as f:
        return json.load(f)


# ── Section 1: Seed counts ────────────────────────────────────────────────────

def test_seed_counts(db):
    print("\n── Seed count checks ─────────────────────────────────────────")

    # Branches
    branches_json = load_json('branches.json')
    db_count = db.query(models.Branch).count()
    check("branches: JSON count == DB count",
          db_count == len(branches_json),
          f"JSON={len(branches_json)}, DB={db_count}")

    # Domains
    domains_json = load_json('domains.json')
    db_count = db.query(models.Domain).count()
    check("domains: JSON count == DB count",
          db_count == len(domains_json),
          f"JSON={len(domains_json)}, DB={db_count}")

    # Achievements
    ach_json = load_json('achievements.json')
    db_count = db.query(models.Achievement).count()
    check("achievements: JSON count == DB count",
          db_count == len(ach_json),
          f"JSON={len(ach_json)}, DB={db_count}")

    # XP levels
    xp_data = load_json('xp_rules.json')
    levels_json = xp_data.get('levels', [])
    db_count = db.query(models.XpLevel).count()
    check("xp_levels: JSON count == DB count",
          db_count == len(levels_json),
          f"JSON={len(levels_json)}, DB={db_count}")

    # XP action rules
    actions_json = {k: v for k, v in xp_data.items() if k != 'levels'}
    db_count = db.query(models.XpActionRule).count()
    check("xp_action_rules: JSON count == DB count",
          db_count == len(actions_json),
          f"JSON={len(actions_json)}, DB={db_count}")

    # Motivational messages
    msg_data = load_json('motivational_messages.json')
    total_msgs = sum(len(v) for v in msg_data.values())
    db_count = db.query(models.MotivationalMessage).count()
    check("motivational_messages: JSON count == DB count",
          db_count == total_msgs,
          f"JSON={total_msgs}, DB={db_count}")

    # Projects
    proj_json = load_json('projects.json')
    db_count = db.query(models.Project).count()
    check("projects: JSON count == DB count",
          db_count == len(proj_json),
          f"JSON={len(proj_json)}, DB={db_count}")

    # Project prerequisites
    pre_data = load_json('prerequisites.json')
    total_pre = sum(
        len(v.get('required', [])) + len(v.get('recommended', []))
        for v in pre_data.values()
    )
    db_count = db.query(models.ProjectPrerequisite).count()
    check("project_prerequisites: JSON count == DB count",
          db_count == total_pre,
          f"JSON={total_pre}, DB={db_count}")

    # Milestones (may be empty)
    ms_json = load_json('milestones.json')
    db_count = db.query(models.Milestone).count()
    check("milestones: JSON count == DB count",
          db_count == len(ms_json),
          f"JSON={len(ms_json)}, DB={db_count}")

    # Users
    users_json = load_json('users.json')
    db_count = db.query(models.User).count()
    check("users: JSON count == DB count",
          db_count == len(users_json),
          f"JSON={len(users_json)}, DB={db_count}")

    # Discussions
    disc_json = load_json('discussions.json')
    db_count = db.query(models.Discussion).count()
    check("discussions: JSON count == DB count",
          db_count == len(disc_json if isinstance(disc_json, list) else []),
          f"JSON={len(disc_json) if isinstance(disc_json, list) else 0}, DB={db_count}")

    # Showcases
    show_json = load_json('showcases.json')
    db_count = db.query(models.Showcase).count()
    check("showcases: JSON count == DB count",
          db_count == len(show_json if isinstance(show_json, list) else []),
          f"JSON={len(show_json) if isinstance(show_json, list) else 0}, DB={db_count}")


# ── Section 2: CRUD cycles ────────────────────────────────────────────────────

def test_domain_crud(db):
    print("\n── Domain CRUD ───────────────────────────────────────────────")
    uid = f"test-domain-{uuid.uuid4().hex[:6]}"

    d = ref_repo.create_domain(db, id=uid, name=f"Test Domain {uid}",
                               icon="🧪", description="Test", color="#fff")
    check("create_domain: returned object", d is not None)
    check("create_domain: id matches", d.id == uid)

    fetched = ref_repo.get_domain(db, uid)
    check("get_domain: found", fetched is not None)
    check("get_domain: name matches", fetched.name == f"Test Domain {uid}")

    updated = ref_repo.update_domain(db, uid, color="#000", description="Updated")
    check("update_domain: color updated", updated.color == "#000")
    check("update_domain: description updated", updated.description == "Updated")

    deleted = ref_repo.delete_domain(db, uid)
    check("delete_domain: returns True", deleted)
    check("delete_domain: no longer found", ref_repo.get_domain(db, uid) is None)


def test_branch_crud(db):
    print("\n── Branch CRUD ───────────────────────────────────────────────")
    uid = f"TEST-{uuid.uuid4().hex[:4]}"
    b = ref_repo.create_branch(db, id=uid, name=f"Test Branch {uid}", short_name=uid)
    check("create_branch: returned", b is not None)
    fetched = ref_repo.get_branch(db, uid)
    check("get_branch: found", fetched is not None)
    updated = ref_repo.update_branch(db, uid, name="Updated Branch")
    check("update_branch: name updated", updated.name == "Updated Branch")
    deleted = ref_repo.delete_branch(db, uid)
    check("delete_branch: returns True", deleted)
    check("delete_branch: gone", ref_repo.get_branch(db, uid) is None)


def test_achievement_crud(db):
    print("\n── Achievement CRUD ──────────────────────────────────────────")
    uid = f"test-ach-{uuid.uuid4().hex[:6]}"
    a = ref_repo.create_achievement(db, id=uid, name=f"Test Ach {uid}",
                                    description="desc", xp_reward=99)
    check("create_achievement: returned", a is not None)
    fetched = ref_repo.get_achievement(db, uid)
    check("get_achievement: found", fetched is not None)
    updated = ref_repo.update_achievement(db, uid, xp_reward=200)
    check("update_achievement: xp_reward updated", updated.xp_reward == 200)
    deleted = ref_repo.delete_achievement(db, uid)
    check("delete_achievement: True", deleted)
    check("delete_achievement: gone", ref_repo.get_achievement(db, uid) is None)


def test_xp_level_crud(db):
    print("\n── XpLevel CRUD ──────────────────────────────────────────────")
    # Use a level number unlikely to exist
    lvl_num = 99
    # clean up if from previous run
    existing = ref_repo.get_xp_level(db, lvl_num)
    if existing:
        ref_repo.delete_xp_level(db, lvl_num)

    lvl = ref_repo.create_xp_level(db, level=lvl_num, name="Test Level", min_xp=99999)
    check("create_xp_level: returned", lvl is not None)
    fetched = ref_repo.get_xp_level(db, lvl_num)
    check("get_xp_level: found", fetched is not None)
    updated = ref_repo.update_xp_level(db, lvl_num, name="Updated Level")
    check("update_xp_level: name updated", updated.name == "Updated Level")
    deleted = ref_repo.delete_xp_level(db, lvl_num)
    check("delete_xp_level: True", deleted)
    check("delete_xp_level: gone", ref_repo.get_xp_level(db, lvl_num) is None)


def test_xp_action_rule_crud(db):
    print("\n── XpActionRule CRUD ─────────────────────────────────────────")
    action = f"test_action_{uuid.uuid4().hex[:6]}"
    r = ref_repo.create_xp_action_rule(db, action=action, xp_value=42)
    check("create_xp_action_rule: returned", r is not None)
    fetched = ref_repo.get_xp_action_rule(db, action)
    check("get_xp_action_rule: found", fetched is not None)
    updated = ref_repo.update_xp_action_rule(db, action, xp_value=100)
    check("update_xp_action_rule: value updated", updated.xp_value == 100)
    deleted = ref_repo.delete_xp_action_rule(db, action)
    check("delete_xp_action_rule: True", deleted)
    check("delete_xp_action_rule: gone", ref_repo.get_xp_action_rule(db, action) is None)


def test_motivational_message_crud(db):
    print("\n── MotivationalMessage CRUD ──────────────────────────────────")
    msg = ref_repo.create_motivational_message(db, category="milestone", message="Test message!")
    check("create_motivational_message: returned", msg is not None)
    check("create_motivational_message: id is int", isinstance(msg.id, int))
    fetched = ref_repo.get_motivational_message(db, msg.id)
    check("get_motivational_message: found", fetched is not None)
    updated = ref_repo.update_motivational_message(db, msg.id, message="Updated!")
    check("update_motivational_message: updated", updated.message == "Updated!")
    deleted = ref_repo.delete_motivational_message(db, msg.id)
    check("delete_motivational_message: True", deleted)
    check("delete_motivational_message: gone",
          ref_repo.get_motivational_message(db, msg.id) is None)


def test_project_crud(db):
    print("\n── Project CRUD ──────────────────────────────────────────────")
    pid = f"test-{uuid.uuid4().hex[:8]}"
    p = prj_repo.create_project(
        db,
        id=pid,
        domain_id="web-development",
        title=f"Test Project {pid}",
        difficulty="beginner",
        level=1,
        type="Test",
        branches=["CSE"],
        technologies=["HTML"],
        description="A test project",
        why_build_this="Testing",
        what_you_learn=["testing"],
        prerequisites=[],
        estimated_hours=1,
        milestone_ids=[],
    )
    check("create_project: returned", p is not None)
    check("create_project: id matches", p.id == pid)

    fetched = prj_repo.get_project(db, pid)
    check("get_project: found", fetched is not None)
    check("get_project: branches deserialisable",
          isinstance(json.loads(fetched.branches), list))

    updated = prj_repo.update_project(db, pid, estimated_hours=5, description="Updated desc")
    check("update_project: hours updated", updated.estimated_hours == 5)
    check("update_project: description updated", updated.description == "Updated desc")

    deleted = prj_repo.delete_project(db, pid)
    check("delete_project: True", deleted)
    check("delete_project: gone", prj_repo.get_project(db, pid) is None)


def test_user_crud(db):
    print("\n── User CRUD ─────────────────────────────────────────────────")
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    uid = str(uuid.uuid4())
    email = f"test_{uuid.uuid4().hex[:6]}@example.com"

    u = usr_repo.create_user(
        db,
        id=uid,
        name="Test User",
        email=email,
        password_hash="hashed_password",
        degree="B.Tech",
        branch_id="CSE",
        semester="Semester 1",
        skill_level="beginner",
        interested_domains=["web-development"],
        goals=["learn"],
        xp=0,
        onboarding_complete=False,
        active_days=[],
        copilot_used=False,
        created_at=now,
        updated_at=now,
    )
    check("create_user: returned", u is not None)
    check("create_user: email matches", u.email == email)

    fetched = usr_repo.get_user(db, uid)
    check("get_user: found", fetched is not None)

    fetched_by_email = usr_repo.get_user_by_email(db, email)
    check("get_user_by_email: found", fetched_by_email is not None)

    updated = usr_repo.update_user(db, uid, xp=100, name="Updated Name")
    check("update_user: xp updated", updated.xp == 100)
    check("update_user: name updated", updated.name == "Updated Name")

    # Test UserProject sub-entities
    up = usr_repo.create_user_project(db, user_id=uid, project_id="web-001",
                                      started_at=now, progress=0.0, status="active")
    check("create_user_project: returned", up is not None)
    fetched_up = usr_repo.get_user_project(db, uid, "web-001")
    check("get_user_project: found", fetched_up is not None)
    updated_up = usr_repo.update_user_project(db, uid, "web-001", progress=50.0)
    check("update_user_project: progress updated", updated_up.progress == 50.0)

    # Test UserProjectMilestone
    upm = usr_repo.create_user_project_milestone(
        db, user_id=uid, project_id="web-001",
        milestone_id="web-001-m01", status="available"
    )
    check("create_user_project_milestone: returned", upm is not None)
    updated_upm = usr_repo.update_user_project_milestone(
        db, uid, "web-001", "web-001-m01", "completed"
    )
    check("update_user_project_milestone: status updated",
          updated_upm.status == "completed")

    # Test UserAchievement
    ua = usr_repo.create_user_achievement(db, user_id=uid,
                                          achievement_id="first-build",
                                          unlocked_at=now)
    check("create_user_achievement: returned", ua is not None)

    del_ua = usr_repo.delete_user_achievement(db, uid, "first-build")
    check("delete_user_achievement: True", del_ua)

    del_upm = usr_repo.delete_user_project_milestone(db, uid, "web-001", "web-001-m01")
    check("delete_user_project_milestone: True", del_upm)

    del_up = usr_repo.delete_user_project(db, uid, "web-001")
    check("delete_user_project: True", del_up)

    deleted = usr_repo.delete_user(db, uid)
    check("delete_user: True", deleted)
    check("delete_user: gone", usr_repo.get_user(db, uid) is None)


def test_community_crud(db):
    print("\n── Community CRUD ────────────────────────────────────────────")
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

    # We need an existing user and project for FKs
    existing_user = db.query(models.User).first()
    existing_proj = db.query(models.Project).first()
    if not existing_user or not existing_proj:
        check("community tests: skipped (no seed data)", False,
              "Need at least 1 user and 1 project")
        return

    disc_id = str(uuid.uuid4())
    disc = com_repo.create_discussion(
        db, id=disc_id, project_id=existing_proj.id,
        user_id=existing_user.id, user_name=existing_user.name,
        content="Test discussion content", created_at=now,
        title="Test Discussion",
    )
    check("create_discussion: returned", disc is not None)
    fetched = com_repo.get_discussion(db, disc_id)
    check("get_discussion: found", fetched is not None)
    updated = com_repo.update_discussion(db, disc_id, upvotes=5)
    check("update_discussion: upvotes updated", updated.upvotes == 5)

    # Showcase
    show_id = str(uuid.uuid4())
    show = com_repo.create_showcase(
        db, id=show_id, user_id=existing_user.id,
        user_name=existing_user.name, project_id=existing_proj.id,
        project_name=existing_proj.title, description="My showcase",
        technologies=["HTML", "CSS"], screenshot_url="",
        demo_url="", github_url="", what_i_learned="Many things",
        challenges_faced="Several", created_at=now,
    )
    check("create_showcase: returned", show is not None)
    fetched_show = com_repo.get_showcase(db, show_id)
    check("get_showcase: found", fetched_show is not None)
    updated_show = com_repo.update_showcase(db, show_id, description="Updated desc")
    check("update_showcase: description updated", updated_show.description == "Updated desc")
    del_show = com_repo.delete_showcase(db, show_id)
    check("delete_showcase: True", del_show)

    del_disc = com_repo.delete_discussion(db, disc_id)
    check("delete_discussion: True", del_disc)
    check("delete_discussion: gone", com_repo.get_discussion(db, disc_id) is None)


def test_list_functions(db):
    """Quick smoke-test of all list functions."""
    print("\n── List functions smoke test ──────────────────────────────────")
    check("list_domains: returns list", isinstance(ref_repo.list_domains(db), list))
    check("list_branches: returns list", isinstance(ref_repo.list_branches(db), list))
    check("list_achievements: returns list", isinstance(ref_repo.list_achievements(db), list))
    check("list_xp_levels: returns list", isinstance(ref_repo.list_xp_levels(db), list))
    check("list_xp_action_rules: returns list",
          isinstance(ref_repo.list_xp_action_rules(db), list))
    check("list_motivational_messages: returns list",
          isinstance(ref_repo.list_motivational_messages(db), list))
    check("list_projects (all): returns list",
          isinstance(prj_repo.list_projects(db), list))
    check("list_projects (filter domain): subset",
          all(p.domain_id == "web-development"
              for p in prj_repo.list_projects(db, domain="web-development")))
    check("list_users: returns list", isinstance(usr_repo.list_users(db), list))
    check("list_showcases: returns list", isinstance(com_repo.list_showcases(db), list))
    check("list_discussions: returns list", isinstance(com_repo.list_discussions(db), list))


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    db = SessionLocal()
    try:
        test_seed_counts(db)
        test_domain_crud(db)
        test_branch_crud(db)
        test_achievement_crud(db)
        test_xp_level_crud(db)
        test_xp_action_rule_crud(db)
        test_motivational_message_crud(db)
        test_project_crud(db)
        test_user_crud(db)
        test_community_crud(db)
        test_list_functions(db)

        db.rollback()  # don't persist test data

    except Exception as e:
        db.rollback()
        print(f"\nFATAL ERROR: {e}")
        traceback.print_exc()
    finally:
        db.close()

    print("\n" + "=" * 60)
    passed = sum(1 for s, _, _ in results if s == PASS)
    failed = sum(1 for s, _, _ in results if s == FAIL)
    print(f"Results: {passed} passed, {failed} failed out of {len(results)} checks")
    if failed:
        print("\nFailed checks:")
        for status, label, detail in results:
            if status == FAIL:
                print(f"  ✗ {label}" + (f"  [{detail}]" if detail else ""))
    print("=" * 60)
    sys.exit(0 if failed == 0 else 1)


if __name__ == '__main__':
    main()
