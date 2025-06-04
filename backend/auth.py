# backend/auth.py

import os
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session # Import Session for type hinting in authenticate_user

# Import necessary modules from your backend package
from backend import models, schemas
# Import specific functions from crud and utils to avoid circular imports
from backend.crud import get_user_by_email # Import only what's needed from crud
from backend.utils import get_password_hash, verify_password # Import password functions from utils

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# JWT configuration
# SECRET_KEY should be loaded from environment variables in production
SECRET_KEY = os.environ.get("SECRET_KEY", "your-super-secret-key-please-change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # Token expiration time in minutes

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Creates a JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user(db: Session, email: str, password: str) -> Optional[models.User]:
    """
    Authenticates a user by email and password.
    """
    user = get_user_by_email(db, email) # Use the imported get_user_by_email from crud
    if not user or not verify_password(password, user.hashed_password): # Use verify_password from utils
        return None
    return user

# This function is used as a dependency to get the current authenticated user
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(Session)) -> models.User:
    """
    Decodes the JWT token and retrieves the current user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        user = get_user_by_email(db, email) # Use the imported get_user_by_email from crud
        if user is None:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception
