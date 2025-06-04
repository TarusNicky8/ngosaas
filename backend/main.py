# backend/main.py

import os
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# Remove StaticFiles if you are no longer serving uploads directly from FastAPI
# from fastapi.staticfiles import StaticFiles # <--- REMOVED THIS LINE

from sqlalchemy.orm import Session
from jose import JWTError, jwt
from uuid import uuid4 # For unique filenames

# For Supabase integration
from supabase import create_client, Client
from typing import List, Annotated, Optional
from datetime import timedelta

# Corrected imports for internal modules
# Ensure these are relative if backend/main.py is at the root on Render
# However, with PYTHONPATH=backend, these should work as is.
from backend import models, schemas, utils, auth, grantee, reviewer, admin
from backend.database import engine, SessionLocal
# Import the new mapping function
from backend.schemas import map_document_model_to_out_schema

# Create all database tables (if they don't exist)
models.Base.metadata.create_all(bind=engine)

# Instantiate the FastAPI app
app = FastAPI()

# Include routers - These already handle the role-specific endpoints
# app.include_router(auth.router) # <--- REMOVED THIS LINE
app.include_router(grantee.router)
app.include_router(reviewer.router)
app.include_router(admin.router)

# CORS Configuration
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000,http://localhost:5173")
origins = [origin.strip() for origin in FRONTEND_URL.split(',')]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- REMOVED STATIC FILES MOUNTING IF YOU ARE USING SUPABASE STORAGE ---
# If you still need to serve other static files from FastAPI, keep this part
# UPLOAD_FOLDER = "uploads"
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# app.mount("/uploads", StaticFiles(directory=UPLOAD_FOLDER), name="uploads")
# --- END REMOVED STATIC FILES ---


# OAuth2 configuration (using auth.py's SECRET_KEY and ALGORITHM)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login") # Changed to relative path "login"

# Supabase Configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_STORAGE_BUCKET = os.environ.get("SUPABASE_STORAGE_BUCKET", "documents")

supabase_client: Optional[Client] = None
if SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY:
    try:
        supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        print("Supabase client initialized successfully.")
    except Exception as e:
        print(f"Error initializing Supabase client: {e}")
        supabase_client = None
else:
    print("Supabase credentials not found in environment variables. Supabase operations will be disabled.")


# Helper function to upload file to Supabase Storage
async def upload_file_to_supabase(file: UploadFile):
    if not supabase_client:
        raise HTTPException(status_code=500, detail="Supabase client not configured.")

    file_extension = os.path.splitext(file.filename)[1]
    supabase_filename = f"{uuid4()}{file_extension}"

    try:
        response = supabase_client.storage.from_(SUPABASE_STORAGE_BUCKET).upload(
            file=await file.read(),
            path=supabase_filename,
            file_options={"content-type": file.content_type}
        )

        if response and "Key" in response:
            public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_STORAGE_BUCKET}/{supabase_filename}"
            return public_url, supabase_filename
        else:
            print(f"Supabase upload error: {response}")
            raise HTTPException(status_code=500, detail=f"Failed to upload file to Supabase Storage: {response}")
    except Exception as e:
        print(f"An unexpected error occurred during Supabase upload: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during Supabase upload: {e}")


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# These are now imported from auth.py
SECRET_KEY = auth.SECRET_KEY
ALGORITHM = auth.ALGORITHM

# Helper function to get current user (used by other routers via dependencies.py)
# This is a core dependency, so it's fine to keep it here or move to dependencies.py
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    # Use auth.get_current_user which now handles token decoding and user retrieval
    return auth.get_current_user(db, token)


# Helper function to get current active user (for protected routes)
async def get_current_active_user(current_user: Annotated[models.User, Depends(get_current_user)]):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# Helper function to get current admin user
async def get_current_admin_user(current_user: Annotated[models.User, Depends(get_current_active_user)]):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform this action. Admin role required."
        )
    return current_user

# Helper function to get current reviewer user
async def get_current_reviewer_user(current_user: Annotated[models.User, Depends(get_current_active_user)]):
    if current_user.role != "reviewer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform this action. Reviewer role required."
        )
    return current_user

# Helper function to get current grantee user
async def get_current_grantee_user(current_user: Annotated[models.User, Depends(get_current_active_user)]):
    if current_user.role != "grantee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform this action. Grantee role required."
        )
    return current_user

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "🚀 FastAPI backend is running!"}

# Registration endpoint
@app.post("/register", status_code=201, response_model=schemas.UserOut, operation_id="register_user_account")
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    # crud.create_user now returns models.User, convert to schemas.UserOut
    return schemas.UserOut.from_orm(crud.create_user(db=db, user=user))

# Login endpoint
@app.post("/login", response_model=schemas.Token)
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email, "id": user.id, "role": user.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Dashboard endpoint
@app.get("/dashboard")
async def read_dashboard(current_user: Annotated[models.User, Depends(get_current_active_user)]):
    return {"message": f"Welcome to your dashboard, {current_user.email}!", "role": current_user.role}

# Grantee Endpoints
@app.post("/grantee/upload", response_model=schemas.DocumentOut)
async def upload_document_route(
    title: Annotated[str, Form()],
    organization: Annotated[str, Form()],
    file: UploadFile,
    current_user: Annotated[models.User, Depends(get_current_grantee_user)],
    db: Session = Depends(get_db)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    supabase_url, supabase_filename = await upload_file_to_supabase(file)

    document_data = schemas.DocumentCreate(
        title=title,
        organization=organization,
        filename=supabase_filename,
        url=supabase_url,
        grantee_id=current_user.id
    )
    db_document_model = crud.create_document(db=db, document=document_data)
    # Map the returned model to the Pydantic schema for the response
    return map_document_model_to_out_schema(db_document_model)


@app.get("/grantee/documents", response_model=List[schemas.DocumentOut])
async def get_grantee_documents(
    current_user: Annotated[models.User, Depends(get_current_grantee_user)],
    db: Session = Depends(get_db)
):
    print(f"[GET DOCS] User: {current_user.id} ({current_user.email}), Role: {current_user.role}")
    documents_models = crud.get_documents_by_grantee(db, grantee_id=current_user.id)
    print(f"[GET DOCS] Found {len(documents_models)} documents for Grantee ID={current_user.id}")
    # Map the list of models to list of Pydantic schemas
    return [map_document_model_to_out_schema(doc_model) for doc_model in documents_models]


# Reviewer Endpoints
@app.get("/reviewer/documents", response_model=List[schemas.DocumentOut])
async def get_reviewer_documents(
    current_user: Annotated[models.User, Depends(get_current_reviewer_user)],
    db: Session = Depends(get_db)
):
    print(f"[REVIEWER DOCS] User: {current_user.id} ({current_user.email}), Role: {current_user.role}")
    documents_models = crud.get_documents_by_reviewer(db, reviewer_id=current_user.id)
    print(f"[REVIEWER DOCS] Found {len(documents_models)} documents for Reviewer ID={current_user.id}")
    # Map the list of models to list of Pydantic schemas
    return [map_document_model_to_out_schema(doc_model) for doc_model in documents_models]


@app.post("/reviewer/documents/{document_id}/evaluate", response_model=schemas.EvaluationOut)
async def submit_document_evaluation(
    document_id: int,
    evaluation: schemas.EvaluationCreate,
    current_user: Annotated[models.User, Depends(get_current_reviewer_user)],
    db: Session = Depends(get_db)
):
    db_evaluation = crud.create_evaluation(
        db=db,
        document_id=document_id,
        reviewer_id=current_user.id,
        comment=evaluation.comment,
        status=evaluation.status
    )
    return schemas.EvaluationOut.from_orm(db_evaluation)

# Admin Endpoints
@app.get("/admin/users", response_model=List[schemas.UserOut])
async def list_users(
    current_user: Annotated[models.User, Depends(get_current_admin_user)],
    db: Session = Depends(get_db)
):
    print(f"[ADMIN] User: {current_user.id} ({current_user.email}), Role: {current_user.role} is listing all users.")
    users_models = crud.get_all_users(db)
    # Map the list of models to list of Pydantic schemas
    return [schemas.UserOut.from_orm(user_model) for user_model in users_models]

@app.get("/admin/documents", response_model=List[schemas.DocumentOut])
async def list_documents(
    current_user: Annotated[models.User, Depends(get_current_admin_user)],
    db: Session = Depends(get_db)
):
    print(f"[ADMIN] User: {current_user.id} ({current_user.email}), Role: {current_user.role} is listing all documents.")
    documents_models = crud.get_all_documents(db)
    # Map the list of models to list of Pydantic schemas
    return [map_document_model_to_out_schema(doc_model) for doc_model in documents_models]

@app.post("/admin/documents/{document_id}/assign_reviewer", response_model=schemas.DocumentOut)
async def assign_reviewer_to_document_route(
    document_id: int,
    assign_data: schemas.AssignReviewer,
    current_user: Annotated[models.User, Depends(get_current_admin_user)],
    db: Session = Depends(get_db)
):
    db_document_model = crud.assign_reviewer_to_document(db, document_id, assign_data.reviewer_id)
    if not db_document_model:
        raise HTTPException(status_code=404, detail="Document not found")

    # Map the returned model to the Pydantic schema for the response
    return map_document_model_to_out_schema(db_document_model)
