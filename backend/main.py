# main.py

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session # joinedload is not needed here as crud handles it
from jose import JWTError, jwt
import os # Ensure os module is imported
from uuid import uuid4

from . import models, schemas, utils, auth, grantee, reviewer, admin
from .database import engine, SessionLocal

# Instantiate the FastAPI app
app = FastAPI()

# Include routers - These already handle the role-specific endpoints
app.include_router(auth.router)
app.include_router(grantee.router)
app.include_router(reviewer.router)
app.include_router(admin.router) # This is already correctly included

# Middleware configuration
# Get allowed origins from environment variable, default to common ones for local development.
# You will set REACT_APP_FRONTEND_URL on Vercel and FRONTEND_URL on Render.
# In production, `FRONTEND_URL` on Render will point to your Vercel app's URL.
allowed_origins = os.environ.get("FRONTEND_URL", "http://localhost:3000,http://localhost:5173").split(',')

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins, # Dynamically set allowed origins
    allow_credentials=True,
    allow_methods=["*"], # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"], # Allow all headers
)

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
# This is a core dependency, so it's fine to keep it here or move to dependencies.py
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

# Registration endpoint - This is fine to keep here or move to auth.py
@app.post("/register", status_code=201)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pw = utils.hash_password(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_pw, role=user.role)
    db.add(db_user)
    db.commit()
    return {"message": "User created successfully"}

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