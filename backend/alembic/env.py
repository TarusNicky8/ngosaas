# backend/alembic/env.py

from logging.config import fileConfig
import os # Added for path manipulation
import sys # Added for sys.path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# This is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- MODIFICATION STARTS HERE ---
# Add the project root to sys.path to allow imports like 'backend.database'
# This assumes env.py is in backend/alembic/ and the project root is two levels up.
# This ensures that when Alembic runs from backend/, it can find 'backend' as a package.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- MODIFICATION ENDS HERE ---

from backend.database import Base # Import your Base from backend.database
target_metadata = Base.metadata # <--- THIS IS THE CRITICAL LINE FOR AUTOGENERATE

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here send the SQL to the
    console, which our setup uses to output transitions
    to the primary database URL.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    # Get the database URL from alembic.ini directly for local operations.
    # This bypasses environment variable issues for local Alembic runs.
    db_url = config.get_main_option("sqlalchemy.url")

    if db_url is None:
        raise Exception("Database URL not found. Please set sqlalchemy.url in alembic.ini")

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        url=db_url, # Use the determined db_url here
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True, # Important for detecting type changes
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
