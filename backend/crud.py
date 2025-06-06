# backend/crud.py

from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
import uuid # ADDED: Import uuid

# Assuming models.py defines the SQLAlchemy models and schemas.py defines Pydantic schemas
from . import models, schemas
# Import password hashing/verification from utils, NOT from auth
from backend.utils import get_password_hash, verify_password

# --- User CRUD Operations ---
def get_user(db: Session, user_id: uuid.UUID) -> Optional[models.User]: # UPDATED: user_id type to uuid.UUID
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
    hashed_password = get_password_hash(user.password) # Use hash function from utils
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
    Handles converting string UUIDs from schema to uuid.UUID objects for model.
    """
    # CRUCIAL FIX: Convert grantee_id and assigned_reviewer_id from string to uuid.UUID
    # before creating the model instance.
    grantee_uuid = uuid.UUID(document.grantee_id)
    assigned_reviewer_uuid = uuid.UUID(document.assigned_reviewer_id) if document.assigned_reviewer_id else None

    db_document = models.Document(
        title=document.title,
        organization=document.organization,
        filename=document.filename,
        url=document.url,
        grantee_id=grantee_uuid, # Pass UUID object
        assigned_reviewer_id=assigned_reviewer_uuid # Pass UUID object or None
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

def get_document(db: Session, document_id: int) -> Optional[models.Document]:
    """Get a single document by its ID, eager loading related data."""
    return db.query(models.Document).options(
        joinedload(models.Document.evaluations).joinedload(models.Evaluation.reviewer),
        joinedload(models.Document.uploader),
        joinedload(models.Document.assigned_reviewer_obj)
    ).filter(models.Document.id == document_id).first()

def get_documents_by_grantee(db: Session, grantee_id: uuid.UUID) -> List[models.Document]: # UPDATED: grantee_id type to uuid.UUID
    """Get all documents uploaded by a specific grantee, eager loading related data."""
    return db.query(models.Document).options(
        joinedload(models.Document.evaluations).joinedload(models.Evaluation.reviewer),
        joinedload(models.Document.uploader),
        joinedload(models.Document.assigned_reviewer_obj)
    ).filter(models.Document.grantee_id == grantee_id).all() # Comparison is now UUID == UUID

def get_all_documents(db: Session, skip: int = 0, limit: int = 100) -> List[models.Document]:
    """Get all documents, eager loading related data."""
    return db.query(models.Document).options(
        joinedload(models.Document.evaluations).joinedload(models.Evaluation.reviewer),
        joinedload(models.Document.uploader),
        joinedload(models.Document.assigned_reviewer_obj)
    ).offset(skip).limit(limit).all()

def get_documents_by_reviewer(db: Session, reviewer_id: uuid.UUID) -> List[models.Document]: # UPDATED: reviewer_id type to uuid.UUID
    """Get all documents assigned to a specific reviewer, eager loading related data."""
    return db.query(models.Document).options(
        joinedload(models.Document.evaluations).joinedload(models.Evaluation.reviewer),
        joinedload(models.Document.uploader),
        joinedload(models.Document.assigned_reviewer_obj)
    ).filter(models.Document.assigned_reviewer_id == reviewer_id).all()


def assign_reviewer_to_document(db: Session, document_id: int, reviewer_id: str) -> Optional[models.Document]: # UPDATED: reviewer_id type to str
    """Assigns a reviewer to a specific document."""
    db_document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if db_document:
        # CRUCIAL FIX: Convert reviewer_id from string to uuid.UUID
        db_document.assigned_reviewer_id = uuid.UUID(reviewer_id)
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        # Re-query with eager loading to ensure relationships are fresh for the returned object
        return get_document(db, document_id) # Use the eager-loading get_document helper
    return None

# --- Evaluation CRUD Operations ---
def create_evaluation(db: Session, document_id: int, reviewer_id: uuid.UUID, comment: str, status: str) -> models.Evaluation: # UPDATED: reviewer_id type to uuid.UUID
    """Create a new evaluation for a document."""
    db_evaluation = models.Evaluation(
        document_id=document_id,
        reviewer_id=reviewer_id, # This should already be a uuid.UUID from the calling context if the dependency is correctly set up
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
        joinedload(models.Evaluation.reviewer)
    ).filter(models.Evaluation.document_id == document_id).all()
