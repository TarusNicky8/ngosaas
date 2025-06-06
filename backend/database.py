from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# IMPORTANT: For local Alembic autogenerate, we temporarily force SQLite.
# REMEMBER TO REVERT THIS LINE AFTER GENERATING MIGRATIONS!
# When deployed on Render, the DATABASE_URL environment variable will be set
# with your PostgreSQL connection string.
DATABASE_URL = os.environ.get("DATABASE_URL")

# Configure connect_args based on the database type.
# The 'check_same_thread' argument is specific to SQLite and is not needed for PostgreSQL.
connect_args = {}
if "sqlite" in DATABASE_URL:
    connect_args["check_same_thread"] = False

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()
