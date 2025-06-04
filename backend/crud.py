# backend/crud.py

from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

# Assuming models.py defines the SQLAlchemy models and schemas.py defines Pydantic schemas
from . import models, schemas
# Import password hashing from auth.py, as main.py uses it
from .auth import get_password_hash, verify_password # Ensure verify_password is also available here if needed for crud direct calls.

# --- User CRUD Operations ---
def get_user(db: Session, user_id: int) -> Optional[models.User]:
    """Get a user by their ID."""
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """Get a user by their email address."""
    return db.query(models.User).filter(models.User.email == email).first()

def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> List[models.User]:
    """Get all users with pagination."""
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """Create a new user."""
    hashed_password = get_password_hash(user.password) # Use hash function from auth.py
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name, # Include full_name if available in UserCreate schema
        role=user.role,
        is_active=True # Default to active
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- Document CRUD Operations ---
def create_document(db: Session, document: schemas.DocumentCreate) -> models.Document:
    """
    Create a new document, storing its Supabase filename and URL.
    """
    db_document = models.Document(
        title=document.title,
        organization=document.organization,
        filename=document.filename, # This is the unique filename in Supabase Storage
        url=document.url,           # This is the public URL from Supabase
        grantee_id=document.grantee_id,
        # assigned_reviewer_id will be None initially unless explicitly provided
        assigned_reviewer_id=document.assigned_reviewer_id
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

def get_document(db: Session, document_id: int) -> Optional[models.Document]:
    """Get a single document by its ID, eager loading related data."""
    return db.query(models.Document).options(
        joinedload(models.Document.evaluations).joinedload(models.Evaluation.reviewer), # Renamed to Evaluation
        joinedload(models.Document.uploader), # New relationship name
        joinedload(models.Document.assigned_reviewer_obj) # New relationship name
    ).filter(models.Document.id == document_id).first()

def get_documents_by_grantee(db: Session, grantee_id: int) -> List[models.Document]:
    """Get all documents uploaded by a specific grantee, eager loading related data."""
    return db.query(models.Document).options(
        joinedload(models.Document.evaluations).joinedload(models.Evaluation.reviewer), # Renamed to Evaluation
        joinedload(models.Document.uploader), # New relationship name
        joinedload(models.Document.assigned_reviewer_obj) # New relationship name
    ).filter(models.Document.grantee_id == grantee_id).all()

def get_all_documents(db: Session, skip: int = 0, limit: int = 100) -> List[models.Document]:
    """Get all documents, eager loading related data."""
    return db.query(models.Document).options(
        joinedload(models.Document.evaluations).joinedload(models.Evaluation.reviewer), # Renamed to Evaluation
        joinedload(models.Document.uploader), # New relationship name
        joinedload(models.Document.assigned_reviewer_obj) # New relationship name
    ).offset(skip).limit(limit).all()

def get_documents_by_reviewer(db: Session, reviewer_id: int) -> List[models.Document]:
    """Get all documents assigned to a specific reviewer, eager loading related data."""
    return db.query(models.Document).options(
        joinedload(models.Document.evaluations).joinedload(models.Evaluation.reviewer), # Renamed to Evaluation
        joinedload(models.Document.uploader), # New relationship name
        joinedload(models.Document.assigned_reviewer_obj) # New relationship name
    ).filter(models.Document.assigned_reviewer_id == reviewer_id).all()


def assign_reviewer_to_document(db: Session, document_id: int, reviewer_id: int) -> Optional[models.Document]:
    """Assigns a reviewer to a specific document."""
    db_document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if db_document:
        db_document.assigned_reviewer_id = reviewer_id
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        # Re-query with eager loading to ensure relationships are fresh for the returned object
        return get_document(db, document_id)
    return None

# --- Evaluation CRUD Operations ---
def create_evaluation(db: Session, document_id: int, reviewer_id: int, comment: str, status: str) -> models.Evaluation:
    """Create a new evaluation for a document."""
    db_evaluation = models.Evaluation( # Renamed from DocumentEvaluation
        document_id=document_id,
        reviewer_id=reviewer_id,
        comment=comment,
        status=status,
    )
    db.add(db_evaluation)
    db.commit()
    db.refresh(db_evaluation)
    return db_evaluation

def get_evaluation(db: Session, evaluation_id: int) -> Optional[models.Evaluation]:
    """Get a single evaluation by its ID."""
    return db.query(models.Evaluation).filter(models.Evaluation.id == evaluation_id).first()

def get_evaluations_for_document(db: Session, document_id: int) -> List[models.Evaluation]:
    """Get all evaluations for a specific document, eager loading the reviewer."""
    return db.query(models.Evaluation).options(
        joinedload(models.Evaluation.reviewer) # Renamed to Evaluation
    ).filter(models.Evaluation.document_id == document_id).all()