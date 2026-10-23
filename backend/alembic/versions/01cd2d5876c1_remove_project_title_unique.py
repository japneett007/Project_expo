"""remove_project_title_unique

Revision ID: 01cd2d5876c1
Revises: 9453deee8c60
Create Date: 2026-10-20 20:14:52.574895

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '01cd2d5876c1'
down_revision: Union[str, Sequence[str], None] = '9453deee8c60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop the UNIQUE constraint on projects.title via raw SQLite DDL.

    The source data has two rows with title='Blog Platform' (different domains).
    SQLite cannot drop a single constraint; we must recreate the table.
    """
    op.execute("""
        CREATE TABLE projects_new (
            id              TEXT NOT NULL PRIMARY KEY,
            domain_id       TEXT NOT NULL REFERENCES domains(id),
            title           TEXT NOT NULL,
            difficulty      TEXT NOT NULL,
            level           INTEGER NOT NULL,
            type            TEXT NOT NULL DEFAULT '',
            branches        TEXT NOT NULL DEFAULT '[]',
            technologies    TEXT NOT NULL DEFAULT '[]',
            description     TEXT NOT NULL DEFAULT '',
            why_build_this  TEXT NOT NULL DEFAULT '',
            what_you_learn  TEXT NOT NULL DEFAULT '[]',
            prerequisites   TEXT NOT NULL DEFAULT '[]',
            estimated_hours INTEGER NOT NULL DEFAULT 0,
            milestone_ids   TEXT NOT NULL DEFAULT '[]',
            CONSTRAINT chk_project_difficulty
                CHECK (difficulty IN ('beginner','intermediate','advanced')),
            CONSTRAINT chk_project_level
                CHECK (level BETWEEN 1 AND 10)
        )
    """)
    op.execute("""
        INSERT INTO projects_new
        SELECT id, domain_id, title, difficulty, level, type, branches,
               technologies, description, why_build_this, what_you_learn,
               prerequisites, estimated_hours, milestone_ids
        FROM projects
    """)
    op.execute("DROP TABLE projects")
    op.execute("ALTER TABLE projects_new RENAME TO projects")


def downgrade() -> None:
    """Restore UNIQUE on projects.title (will fail if duplicate titles exist)."""
    op.execute("""
        CREATE TABLE projects_new (
            id              TEXT NOT NULL PRIMARY KEY,
            domain_id       TEXT NOT NULL REFERENCES domains(id),
            title           TEXT NOT NULL UNIQUE,
            difficulty      TEXT NOT NULL,
            level           INTEGER NOT NULL,
            type            TEXT NOT NULL DEFAULT '',
            branches        TEXT NOT NULL DEFAULT '[]',
            technologies    TEXT NOT NULL DEFAULT '[]',
            description     TEXT NOT NULL DEFAULT '',
            why_build_this  TEXT NOT NULL DEFAULT '',
            what_you_learn  TEXT NOT NULL DEFAULT '[]',
            prerequisites   TEXT NOT NULL DEFAULT '[]',
            estimated_hours INTEGER NOT NULL DEFAULT 0,
            milestone_ids   TEXT NOT NULL DEFAULT '[]',
            CONSTRAINT chk_project_difficulty
                CHECK (difficulty IN ('beginner','intermediate','advanced')),
            CONSTRAINT chk_project_level
                CHECK (level BETWEEN 1 AND 10)
        )
    """)
    op.execute("""
        INSERT INTO projects_new
        SELECT id, domain_id, title, difficulty, level, type, branches,
               technologies, description, why_build_this, what_you_learn,
               prerequisites, estimated_hours, milestone_ids
        FROM projects
    """)
    op.execute("DROP TABLE projects")
    op.execute("ALTER TABLE projects_new RENAME TO projects")
