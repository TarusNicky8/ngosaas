# backend/dependencies.py
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from typing import Generator

# Dependency to get DB session
def get_db() -> Generator:
    """
    Yields a database session to be used in FastAPI path operations.
    Ensures the session is closed after the request is processed.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Removed from this file:
# - SECRET_KEY and ALGORITHM (moved to auth.py)
# - oauth2_scheme (moved to auth.py)
# - get_current_user (moved to auth.py)
# - get_current_active_user (moved to auth.py)
