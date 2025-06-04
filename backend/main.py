# backend/main.py

import os
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# Remove StaticFiles if you are no longer serving uploads directly from FastAPI
# from fastapi.staticfiles import StaticFiles # <--- REMOVE THIS LINE IF YOU ARE USING SUPABASE STORAGE
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from uuid import uuid4 # For unique filenames

# For Supabase integration
from supabase import create_client, Client
from typing import List, Annotated, Optional # Added for type hinting and Annotated
from datetime import timedelta # Added for token expiration in login

# Corrected imports for internal modules
from backend import models, schemas, utils, auth, grantee, reviewer, admin
from backend.database import engine, SessionLocal

# Create all database tables (if they don't exist)
models.Base.metadata.create_all(bind=engine)

# Instantiate the FastAPI app
app = FastAPI()

# Include routers - These already handle the role-specific endpoints
app.include_router(auth.router)
app.include_router(grantee.router)
app.include_router(reviewer.router)
app.include_router(admin.router)

# CORS Configuration
# Get the frontend URL from environment variable for CORS
# This will be set on Render to https://ngosaas-frontend.vercel.app
# For local development, it will default to http://localhost:3000,http://localhost:5173
# Use .split(',') to handle multiple origins if needed
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000,http://localhost:5173")
origins = [origin.strip() for origin in FRONTEND_URL.split(',')]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Use the dynamic origins list
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


# OAuth2 configuration
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login") # Changed to relative path "login"

# Supabase Configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL") # e.g., https://xxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_STORAGE_BUCKET = os.environ.get("SUPABASE_STORAGE_BUCKET", "documents") # Default to 'documents'

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

    # Generate a unique filename
    file_extension = os.path.splitext(file.filename)[1]
    supabase_filename = f"{uuid4()}{file_extension}" # Use uuid4 directly from uuid import

    try:
        # Upload file to Supabase Storage
        # The path will be /{bucket_name}/{supabase_filename}
        response = supabase_client.storage.from_(SUPABASE_STORAGE_BUCKET).upload(
            file=await file.read(),
            path=supabase_filename,
            file_options={"content-type": file.content_type}
        )

        # Supabase client.storage.from_().upload returns a dictionary on success
        # and raises an exception on failure (or returns an error response in some cases).
        # We need to check the structure based on actual supabase-py behavior.
        # Assuming a successful upload returns a dict with 'Key' or similar info.
        # The public URL is constructed manually.
        if response and "Key" in response: # Check for success key in response
            # Construct the public URL
            # Supabase public URL format: {SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{path_to_file}
            public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_STORAGE_BUCKET}/{supabase_filename}"
            return public_url, supabase_filename
        else:
            print(f"Supabase upload error: {response}") # Log the full response for debugging
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

# OAuth2 configuration (using auth.py's SECRET_KEY and ALGORITHM)
SECRET_KEY = auth.SECRET_KEY
ALGORITHM = auth.ALGORITHM

# Helper function to get current user (used by other routers via dependencies.py)
# This is a core dependency, so it's fine to keep it here or move to dependencies.py
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
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
    # Assuming crud.create_user handles hashing and adding to DB
    return crud.create_user(db=db, user=user)

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

    # Upload file to Supabase Storage
    supabase_url, supabase_filename = await upload_file_to_supabase(file)

    # Create document record in DB with Supabase URL and filename
    document_data = schemas.DocumentCreate(
        title=title,
        organization=organization,
        filename=supabase_filename, # Store the unique filename in Supabase Storage
        url=supabase_url, # Store the Supabase public URL
        uploaded_by=current_user.email,
        grantee_id=current_user.id
    )
    db_document = crud.create_document(db=db, document=document_data)
    return db_document

@app.get("/grantee/documents", response_model=List[schemas.DocumentOut])
async def get_grantee_documents(
    current_user: Annotated[models.User, Depends(get_current_grantee_user)],
    db: Session = Depends(get_db)
):
    print(f"[GET DOCS] User: {current_user.id} ({current_user.email}), Role: {current_user.role}")
    documents = crud.get_documents_by_grantee(db, grantee_id=current_user.id)
    print(f"[GET DOCS] Found {len(documents)} documents for Grantee ID={current_user.id}")
    for doc in documents:
        evaluations_data = crud.get_evaluations_for_document(db, document_id=doc.id)
        doc.evaluations = [
            schemas.EvaluationOut(
                id=eval.id,
                comment=eval.comment,
                status=eval.status,
                reviewer_email=eval.reviewer.email if eval.reviewer else None,
                created_at=eval.created_at
            ) for eval in evaluations_data
        ]
        print(f" - Document ID={doc.id}, Title={doc.title}, Organization={doc.organization}, Filename={doc.filename}")
        print(f"   Uploaded By: {doc.uploaded_by}, URL: {doc.url}")
        for eval_data in doc.evaluations:
            print(f"   - Eval ID={eval_data.id}, Reviewer Email={eval_data.reviewer_email}, Comment='{eval_data.comment}', Status={eval_data.status}")
    return documents


# Reviewer Endpoints
@app.get("/reviewer/documents", response_model=List[schemas.DocumentOut])
async def get_reviewer_documents(
    current_user: Annotated[models.User, Depends(get_current_reviewer_user)],
    db: Session = Depends(get_db)
):
    print(f"[REVIEWER DOCS] User: {current_user.id} ({current_user.email}), Role: {current_user.role}")
    # Fetch documents assigned to this specific reviewer
    documents = crud.get_documents_by_reviewer(db, reviewer_id=current_user.id)
    print(f"[REVIEWER DOCS] Found {len(documents)} documents for Reviewer ID={current_user.id}")
    for doc in documents:
        evaluations_data = crud.get_evaluations_for_document(db, document_id=doc.id)
        doc.evaluations = [
            schemas.EvaluationOut(
                id=eval.id,
                comment=eval.comment,
                status=eval.status,
                reviewer_email=eval.reviewer.email if eval.reviewer else None,
                created_at=eval.created_at
            ) for eval in evaluations_data
        ]
        print(f" - Document ID={doc.id}, Title={doc.title}, Organization={doc.organization}, Filename={doc.filename}")
        print(f"   Uploaded By: {doc.uploaded_by}, URL: {doc.url}")
        for eval_data in doc.evaluations:
            print(f"   - Eval ID={eval_data.id}, Reviewer Email={eval_data.reviewer_email}, Comment='{eval_data.comment}', Status={eval_data.status}")
    return documents


@app.post("/reviewer/documents/{document_id}/evaluate", response_model=schemas.EvaluationOut)
async def submit_document_evaluation(
    document_id: int,
    evaluation: schemas.DocumentEvaluationCreate,
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
    return schemas.EvaluationOut(
        id=db_evaluation.id,
        comment=db_evaluation.comment,
        status=db_evaluation.status,
        reviewer_email=current_user.email, # Set current reviewer's email
        created_at=db_evaluation.created_at
    )

# Admin Endpoints
@app.get("/admin/users", response_model=List[schemas.UserOut])
async def list_users(
    current_user: Annotated[models.User, Depends(get_current_admin_user)],
    db: Session = Depends(get_db)
):
    print(f"[ADMIN] User: {current_user.id} ({current_user.email}), Role: {current_user.role} is listing all users.")
    users = crud.get_all_users(db)
    return [schemas.UserOut.from_orm(user) for user in users]

@app.get("/admin/documents", response_model=List[schemas.DocumentOut])
async def list_documents(
    current_user: Annotated[models.User, Depends(get_current_admin_user)],
    db: Session = Depends(get_db)
):
    print(f"[ADMIN] User: {current_user.id} ({current_user.email}), Role: {current_user.role} is listing all documents.")
    documents = crud.get_all_documents(db)
    for doc in documents:
        evaluations_data = crud.get_evaluations_for_document(db, document_id=doc.id)
        doc.evaluations = [
            schemas.EvaluationOut(
                id=eval.id,
                comment=eval.comment,
                status=eval.status,
                reviewer_email=eval.reviewer.email if eval.reviewer else None,
                created_at=eval.created_at
            ) for eval in evaluations_data
        ]
    return documents

@app.post("/admin/documents/{document_id}/assign_reviewer", response_model=schemas.DocumentOut)
async def assign_reviewer_to_document_route(
    document_id: int,
    assign_data: schemas.AssignReviewer,
    current_user: Annotated[models.User, Depends(get_current_admin_user)],
    db: Session = Depends(get_db)
):
    db_document = crud.assign_reviewer_to_document(db, document_id, assign_data.reviewer_id)
    if not db_document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Populate assigned_reviewer_email for the response
    if db_document.assigned_reviewer:
        db_document.assigned_reviewer_email = db_document.assigned_reviewer.email
    else:
        db_document.assigned_reviewer_email = None

    # Also populate evaluations for the response
    evaluations_data = crud.get_evaluations_for_document(db, document_id=db_document.id)
    db_document.evaluations = [
        schemas.EvaluationOut(
            id=eval.id,
            comment=eval.comment,
            status=eval.status,
            reviewer_email=eval.reviewer.email if eval.reviewer else None,
            created_at=eval.created_at
        ) for eval in evaluations_data
    ]

    return db_document