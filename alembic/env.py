"""Alembic environment configuration.

Supports both synchronous (offline) and asynchronous (online) migration modes.
The async mode uses the same SQLAlchemy async engine as the application so there
is no need to maintain a separate sync connection string.
"""
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# Import all models so Alembic autogenerate can detect them.
# ----------------------------------------------------------------
from app.database import Base  # noqa: F401  (registers Base.metadata)
import app.models.user  # noqa: F401
import app.models.book  # noqa: F401
import app.models.borrow  # noqa: F401
# ----------------------------------------------------------------

# Alembic Config object (gives access to values in alembic.ini)
config = context.config

# Set up Python logging from the ini file section.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The MetaData object for autogenerate support.
target_metadata = Base.metadata


def get_url() -> str:
    """Prefer the DATABASE_URL environment variable; fall back to alembic.ini."""
    import os
    return os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))


# ---------------------------------------------------------------------------
# Offline migrations (generate SQL scripts without a live DB connection)
# ---------------------------------------------------------------------------

def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # required for SQLite ALTER TABLE support
    )
    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migrations (connect to a live DB and apply changes)
# ---------------------------------------------------------------------------

def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,  # required for SQLite ALTER TABLE support
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
