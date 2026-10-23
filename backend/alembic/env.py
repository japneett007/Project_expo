"""
Alembic environment configuration.

Wired to:
  - DATABASE_URL from .env (via database.py)
  - All ORM models via Base.metadata (from models.py)
"""
import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy import engine_from_config

from alembic import context

# Make sure backend/ is on sys.path so we can import database and models
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import DATABASE_URL, Base  # noqa: E402
import models  # noqa: E402, F401  — registers all ORM classes
_ = models

# Alembic Config object
alembic_config = context.config

# Set the sqlalchemy.url from our env-driven value
alembic_config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Set up loggers from alembic.ini
if alembic_config.config_file_name is not None:
    fileConfig(alembic_config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run in 'offline' mode — writes SQL to stdout without a live connection."""
    url = alembic_config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,   # required for SQLite ALTER TABLE support
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run in 'online' mode — uses a live database connection."""
    connectable = engine_from_config(
        alembic_config.get_section(alembic_config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,   # required for SQLite ALTER TABLE support
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()