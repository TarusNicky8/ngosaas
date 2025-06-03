# main.py

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles # <--- THIS LINE IS NOW ADDED/UNCOMMENTED
from sqlalchemy.orm import Session
from jose import JWTError, jwt
import os
from uuid import uuid4

# Corrected imports: Ensure these are relative if backend/main.py is at the root on Render
# However, with PYTHONPATH=backend, these should work as is.
from backend import models, schemas, utils, auth, grantee, reviewer, admin
from backend.database import engine, SessionLocal # Use backend.database as it's within the backend package

# Instantiate the FastAPI app
app = FastAPI()

# Include routers - These already handle the role-specific endpoints
app.include_router(auth.router)
app.include_router(grantee.router)
app.include_router(reviewer.router)
app.include_router(admin.router)

# --- CRUCIAL CORRECTION FOR CORS ---
# Get the frontend URL from environment variable for CORS
# This will be set on Render to https://ngosaas-frontend.vercel.app
# For local development, it will default to http://localhost:3000
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

origins = [
    FRONTEND_URL,
    "http://localhost:3000", # For local frontend development
    "http://localhost:8000", # For local backend testing directly
    # Add any other origins your frontend might be deployed on (e.g., Vercel preview URLs)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Use the dynamic origins list
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- END CORS CORRECTION ---

# Static files configuration
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_FOLDER), name="uploads")

# Database models creation
models.Base.metadata.create_all(bind=engine)

# OAuth2 configuration
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
SECRET_KEY = auth.SECRET_KEY
ALGORITHM = auth.ALGORITHM

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency to get current user (used by other routers via dependencies.py)
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

# Root endpoint - This is fine to keep here
@app.get("/")
def read_root():
    return {"message": "🚀 FastAPI backend is running!"}

# Registration endpoint - ADDED operation_id and response_model for clarity/warnings
@app.post("/register", status_code=201, response_model=schemas.Token, operation_id="register_user_account")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pw = utils.hash_password(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_pw, role=user.role)
    db.add(db_user)
    db.commit()
    # Return a token upon successful registration for immediate login experience
    token_data = {"sub": db_user.email, "role": db_user.role}
    access_token = auth.create_access_token(data=token_data)
    return {"access_token": access_token, "token_type": "bearer"}


# Login endpoint - This is fine to keep here or move to auth.py
@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not utils.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token_data = {"sub": user.email, "role": user.role}
    access_token = auth.create_access_token(data=token_data)
    return {"access_token": access_token, "token_type": "bearer"}

# Dashboard endpoint - This is fine to keep here
@app.get("/dashboard")
def get_dashboard(current_user: models.User = Depends(get_current_user)):
    return {
        "message": f"✅ Welcome to your dashboard, {current_user.email}!",
        "role": current_user.role
    }

# --- REMOVED REDUNDANT ENDPOINTS BELOW ---
# Document upload endpoint - Now handled by grantee.py
# @app.post("/upload-doc")
# async def upload_document(...):
#    ...

# List documents endpoint - Now handled by reviewer.py and admin.py
# @app.get("/documents")
# def list_documents(...):
#    ...

# Evaluate document endpoint - Now handled by reviewer.py
# @app.post("/documents/{doc_id}/evaluate")
# def evaluate_document(...):
#    ...

# Grantee documents endpoint - Now handled by grantee.py
# @app.get("/grantee/documents")
# def get_grantee_documents_with_evaluations(...):
#    ...