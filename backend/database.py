"""
database.py
-----------
Single source of truth for the SQLAlchemy engine and session factory.

Usage
-----
    from database import get_db, engine

    # In a Flask route / repository:
    with get_db() as db:
        result = db.execute(...)

    # In tests / scripts:
    from database import engine
    Base.metadata.create_all(engine)
"""
import os
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

load_dotenv()

# ── Engine ─────────────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

# connect_args only needed for SQLite (enables WAL mode for better concurrency)
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,          # set True to log all SQL statements
)

# Enable WAL mode and foreign-key enforcement for every new SQLite connection
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_conn, _record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# ── Session factory ────────────────────────────────────────────────────────────
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── Declarative base ───────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── Context manager helper ─────────────────────────────────────────────────────
@contextmanager
def get_db():
    """
    Yield a database session and guarantee it is closed when done.

    Example::

        with get_db() as db:
            users = db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ── XP level helper ────────────────────────────────────────────────────────────
def get_user_level_from_db(xp: int, db) -> dict:
    """Return the current XP level dict for a given XP value (reads DB)."""
    from models import XpLevel  # local import avoids circular deps at module load
    levels = db.query(XpLevel).order_by(XpLevel.level).all()
    current = {"level": 1, "name": "Explorer", "minXP": 0}
    for lvl in levels:
        if xp >= lvl.min_xp:
            current = {"level": lvl.level, "name": lvl.name, "minXP": lvl.min_xp}
    return current
