# backend/main.py

import os
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from sqlalchemy.orm import Session # For type hinting
from uuid import uuid4 # For unique filenames for Supabase uploads

# For Supabase integration
from supabase import create_client, Client
from typing import List, Annotated, Optional
from datetime import timedelta

# Import core backend modules
from backend import models, schemas, utils, crud
from backend.database import engine # Only engine is needed for metadata.create_all

# Import dependencies from the dedicated dependencies module
from backend.dependencies import get_db

# Import all authentication and user dependency functions from the auth module
from backend.auth import (
    SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user, create_access_token, # Used directly in login
    get_current_user, get_current_active_user, # Core user dependencies
    get_current_admin_user, get_current_reviewer_user, get_current_grantee_user # Role-specific dependencies
)

# Import the new mapping function
from backend.schemas import map_document_model_to_out_schema

# Create all database tables (if they don't exist)
# This will try to connect to the DB on startup
models.Base.metadata.create_all(bind=engine)

# Instantiate the FastAPI app
app = FastAPI()

# --- CORS Configuration ---
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000,http://localhost:5173")
origins = [origin.strip() for origin in FRONTEND_URL.split(',')]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Supabase Configuration ---
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
    supabase_filename = f"{uuid4()}{file_extension}" # Use uuid4 from 'uuid' module

    try:
        # Perform the upload; this returns an UploadResponse object (dataclass)
        upload_result = supabase_client.storage.from_(SUPABASE_STORAGE_BUCKET).upload(
            file=await file.read(),
            path=supabase_filename,
            file_options={"content-type": file.content_type}
        )

        # Corrected: Check for success using 'path' attribute of the UploadResponse object
        if upload_result and getattr(upload_result, 'path', None): # Safely check if path attribute exists
            public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_STORAGE_BUCKET}/{supabase_filename}"
            print(f"[DEBUG UPLOAD] File uploaded to: {public_url}") # Debug print
            return public_url, supabase_filename
        else:
            # If upload_result doesn't have a path, it likely failed or the response was unexpected
            print(f"Supabase upload error: Upload result missing path: {upload_result}")
            raise HTTPException(status_code=500, detail=f"Failed to upload file to Supabase Storage: Invalid upload response.")
    except Exception as e:
        print(f"An unexpected error occurred during Supabase upload: {e}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during Supabase upload: {e}")

# --- API Endpoints ---

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
    return schemas.UserOut.from_orm(crud.create_user(db=db, user=user))

# Login endpoint
@app.post("/login", response_model=schemas.Token)
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # user.id is already a UUID object here; create_access_token in auth.py will handle conversion
    access_token = create_access_token(
        data={"sub": user.email, "id": user.id, "role": user.role},
        expires_delta=access_token_expires
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
        grantee_id=str(current_user.id) # Convert current_user.id to string here
    )
    db_document_model = crud.create_document(db=db, document=document_data)
    return map_document_model_to_out_schema(db_document_model)


@app.get("/grantee/documents", response_model=List[schemas.DocumentOut])
async def get_grantee_documents(
    current_user: Annotated[models.User, Depends(get_current_grantee_user)],
    db: Session = Depends(get_db)
):
    print(f"[GET DOCS] User: {current_user.id} ({current_user.email}), Role: {current_user.role}")
    documents_models = crud.get_documents_by_grantee(db, grantee_id=current_user.id)
    print(f"[GET DOCS] Found {len(documents_models)} documents for Grantee ID={current_user.id}")
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
@app.get("/admin/users", response_model=List[schemas.UserOut], operation_id="list_all_users_admin") # Added unique operation_id
async def list_users(
    current_user: Annotated[models.User, Depends(get_current_admin_user)],
    db: Session = Depends(get_db)
):
    print(f"[ADMIN] User: {current_user.id} ({current_user.email}), Role: {current_user.role} is listing all users.")
    users_models = crud.get_all_users(db)
    return [schemas.UserOut.from_orm(user_model) for user_model in users_models]

@app.get("/admin/documents", response_model=List[schemas.DocumentOut])
async def list_documents(
    current_user: Annotated[models.User, Depends(get_current_admin_user)],
    db: Session = Depends(get_db)
):
    print(f"[ADMIN] User: {current_user.id} ({current_user.email}), Role: {current_user.role} is listing all documents.")
    documents_models = crud.get_all_documents(db)
    return [map_document_model_to_out_schema(doc_model) for doc_model in documents_models]

@app.post("/admin/documents/{document_id}/assign_reviewer", response_model=schemas.DocumentOut)
async def assign_reviewer_to_document_route(
    document_id: int,
    assign_data: schemas.AssignReviewer,
    current_user: Annotated[models.User, Depends(get_current_admin_user)],
    db: Session = Depends(get_db)
):
    print(f"[DEBUG MAIN] Received assignment request for document ID: {document_id}, reviewer ID: {assign_data.reviewer_id}") # ADDED DEBUG
    db_document_model = crud.assign_reviewer_to_document(db, document_id, assign_data.reviewer_id)
    
    if not db_document_model:
        print(f"[DEBUG MAIN] crud.assign_reviewer_to_document returned None for document ID: {document_id}") # ADDED DEBUG
        # Attempt to get the document again to confirm if it exists at all
        existing_document_model = crud.get_document(db, document_id)
        if not existing_document_model:
            print(f"[DEBUG MAIN] Document {document_id} truly not found in DB.") # ADDED DEBUG
            raise HTTPException(status_code=404, detail="Document not found")
        else:
            print(f"[DEBUG MAIN] Document {document_id} EXISTS, but assignment failed (reviewer likely invalid).") # ADDED DEBUG
            raise HTTPException(status_code=400, detail="Failed to assign reviewer. Reviewer might not exist or not have 'reviewer' role.")
    
    print(f"[DEBUG MAIN] Document {document_id} successfully assigned reviewer.") # ADDED DEBUG
    return map_document_model_to_out_schema(db_document_model)
