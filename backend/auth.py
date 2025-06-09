# backend/auth.py

import os
from datetime import datetime, timedelta
from typing import Optional, Annotated
from jose import jwt, JWTError
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
import uuid # Required for UUID to string conversion in JWT payload

from sqlalchemy.orm import Session # For type hinting database session

# Import necessary modules from your backend package
from backend import models, schemas
# Import specific functions from crud and utils
from backend.crud import get_user_by_email # Used for retrieving user by email
from backend.utils import get_password_hash, verify_password # Used for password hashing/verification
from backend.dependencies import get_db # Import the get_db dependency

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login") # This URL must match your actual login endpoint path

# JWT configuration
SECRET_KEY = os.environ.get("SECRET_KEY", "your-super-secret-key-please-change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # Token expiration time in minutes

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Creates a JWT access token with user data.
    Ensures UUID objects (like user IDs) are converted to strings for JSON serialization.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    # CRUCIAL FIX: Convert UUID to string before encoding into JWT payload
    # This resolves TypeError: Object of type UUID is not JSON serializable
    if "id" in to_encode and isinstance(to_encode["id"], uuid.UUID):
        to_encode["id"] = str(to_encode["id"])

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    """
    Authenticates a user by checking email and hashed password.
    """
    user = get_user_by_email(db, email) # Retrieve user from database
    if not user or not verify_password(password, user.hashed_password): # Verify password
        return None
    return user

# --- Core User Dependencies (used across different roles) ---

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    """
    Decodes the JWT token from the request header and retrieves the current user.
    This fixes the 'Session' object has no attribute 'rsplit' error by correctly
    passing the database session using Depends(get_db).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # The jwt.decode function expects a string token and a string key
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"[DEBUG AUTH] JWT Payload: {payload}") # DEBUG PRINT
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        user = get_user_by_email(db, email) # Retrieve user from database
        if user is None:
            raise credentials_exception
        print(f"[DEBUG AUTH] User retrieved from DB in get_current_user: {user.email}, Role: {user.role}, ID: {user.id}") # DEBUG PRINT
        return user
    except JWTError:
        # Catch JWT specific errors (e.g., invalid token, expired token)
        print(f"[DEBUG AUTH] JWTError during token decoding.") # DEBUG PRINT
        raise credentials_exception
    except Exception as e:
        # Catch any other unexpected errors during token processing
        print(f"[DEBUG AUTH] Unexpected error during get_current_user: {e}") # DEBUG PRINT
        raise credentials_exception

async def get_current_active_user(current_user: Annotated[models.User, Depends(get_current_user)]):
    """
    Ensures the retrieved user is active.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# --- Role-Specific User Dependencies ---

async def get_current_admin_user(current_user: Annotated[models.User, Depends(get_current_active_user)]):
    """
    Ensures the current active user has the 'admin' role.
    """
    print(f"[DEBUG AUTH] Checking admin role for user: {current_user.email}, Role: {current_user.role}") # DEBUG PRINT
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform this action. Admin role required."
        )
    return current_user

async def get_current_reviewer_user(current_user: Annotated[models.User, Depends(get_current_active_user)]):
    """
    Ensures the current active user has the 'reviewer' role.
    """
    print(f"[DEBUG AUTH] Checking reviewer role for user: {current_user.email}, Role: {current_user.role}") # DEBUG PRINT
    if current_user.role != "reviewer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform this action. Reviewer role required."
        )
    return current_user

async def get_current_grantee_user(current_user: Annotated[models.User, Depends(get_current_active_user)]):
    """
    Ensures the current active user has the 'grantee' role.
    """
    print(f"[DEBUG AUTH] Checking grantee role for user: {current_user.email}, Role: {current_user.role}") # DEBUG PRINT
    if current_user.role != "grantee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform this action. Grantee role required."
        )
    return current_user
