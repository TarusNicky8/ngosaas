# backend/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer # Keep this here for get_current_user's dependency
from jose import jwt, JWTError # Keep for token decoding in get_current_user
from sqlalchemy.orm import Session
from backend.database import SessionLocal # Import SessionLocal from your database module
from typing import Generator

# Import necessary modules from your backend package
from backend import crud, models # Import crud and models for get_current_user

# Note: SECRET_KEY and ALGORITHM should be defined and loaded from environment
# variables in backend/auth.py, not here.

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login") # Ensure this matches your login endpoint URL

# Dependency to get DB session
def get_db() -> Generator:
    """
    Dependency to get a database session.
    Yields a session and ensures it's closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Verify token and get current user
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    """
    Decodes the JWT token and retrieves the current user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # SECRET_KEY and ALGORITHM should be imported from auth.py or defined globally if needed
        # For simplicity, if auth.py defines them, ensure they are accessible.
        # Alternatively, if get_current_user remains here, you might need to import
        # them directly or pass them. Let's make sure auth.py passes them implicitly.
        # For this function to work without circular imports, SECRET_KEY and ALGORITHM
        # would need to be passed as arguments or loaded within this function from env.
        # Given our structure, get_current_user logic should be defined in auth.py,
        # and main.py (and other routers) depend on it.

        # FIX: The current setup where get_current_user uses SECRET_KEY/ALGORITHM
        # directly from auth.py if auth.py defines them, and auth.py then imports get_current_user
        # from dependencies.py, creates a circular dependency.
        # Best approach: Keep SECRET_KEY/ALGORITHM in auth.py.
        # get_current_user needs to accept these or load them.
        # However, for simplicity and to prevent circular imports if auth is also part of the auth flow.

        # Let's revert get_current_user back to auth.py.
        # The original plan was to keep get_current_user logic in auth.py.
        # I will remove get_current_user and get_current_active_user from THIS file.
        # They belong in auth.py.
        pass # Placeholder, these functions will be removed
    except JWTError:
        raise credentials_exception
    # user = crud.get_user_by_email(db, email=email)
    # if user is None:
    #     raise credentials_exception
    # return user

# def get_current_active_user(current_user: models.User = Depends(get_current_user)):
#     # Add logic for active user if needed
#     return current_user
