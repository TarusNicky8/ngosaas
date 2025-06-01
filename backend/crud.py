# crud.py
from sqlalchemy.orm import Session, joinedload
from passlib.context import CryptContext
from datetime import datetime
from typing import List, Optional # Import Optional for type hints
import models, schemas # Assuming models.py defines the SQLAlchemy models

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Password hashing
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Create user
def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Get user by email
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

# Authenticate user
def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

# Create document
def create_document(db: Session, title: str, organization: str, filename: str, grantee_id: int, user_email: str):
    db_doc = models.Document(
        title=title,
        organization=organization,
        filename=filename,
        grantee_id=grantee_id,
        user_email=user_email,
        uploaded_by=user_email, # Set uploaded_by directly here
        url=f"/uploads/{filename}" # Set url directly here
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    return db_doc

# Helper function to map a SQLAlchemy Document model to a Pydantic DocumentOut schema
def _map_document_to_document_out(doc: models.Document) -> schemas.DocumentOut:
    """Maps a SQLAlchemy Document object to a Pydantic DocumentOut schema."""
    evaluations_out = []
    for eval_item in doc.evaluations:
        reviewer_email = eval_item.reviewer.email if eval_item.reviewer else "Unknown Reviewer"
        evaluations_out.append(schemas.EvaluationOut(
            id=eval_item.id,
            comment=eval_item.comment,
            status=eval_item.status,
            reviewer_email=reviewer_email,
            created_at=eval_item.created_at
        ))

    assigned_reviewer_email = doc.assigned_reviewer.email if doc.assigned_reviewer else None

    return schemas.DocumentOut(
        id=doc.id,
        title=doc.title,
        organization=doc.organization,
        filename=doc.filename,
        user_email=doc.user_email,
        grantee_id=doc.grantee_id,
        uploaded_by=doc.uploaded_by,
        url=doc.url,
        assigned_reviewer_id=doc.assigned_reviewer_id, # Populate new field
        assigned_reviewer_email=assigned_reviewer_email, # Populate new field
        evaluations=evaluations_out
    )

# Get documents for grantee
def get_documents_by_grantee(db: Session, grantee_id: int) -> List[schemas.DocumentOut]:
    documents = db.query(models.Document).options(
        joinedload(models.Document.evaluations).joinedload(models.DocumentEvaluation.reviewer),
        joinedload(models.Document.assigned_reviewer) # Eager load the assigned reviewer
    ).filter(models.Document.grantee_id == grantee_id).all()

    return [_map_document_to_document_out(doc) for doc in documents]

# Get all documents (for reviewer/admin)
def get_all_documents(db: Session) -> List[schemas.DocumentOut]:
    documents = db.query(models.Document).options(
        joinedload(models.Document.evaluations).joinedload(models.DocumentEvaluation.reviewer),
        joinedload(models.Document.assigned_reviewer) # Eager load the assigned reviewer
    ).all()

    return [_map_document_to_document_out(doc) for doc in documents]

# Get document by ID
def get_document_by_id(db: Session, document_id: int) -> Optional[schemas.DocumentOut]:
    document = db.query(models.Document).options(
        joinedload(models.Document.evaluations).joinedload(models.DocumentEvaluation.reviewer),
        joinedload(models.Document.assigned_reviewer) # Eager load the assigned reviewer
    ).filter(models.Document.id == document_id).first()

    if document:
        return _map_document_to_document_out(document)
    return None

# Create evaluation
def create_evaluation(db: Session, document_id: int, reviewer_id: int, evaluation: schemas.EvaluationCreate):
    db_eval = models.DocumentEvaluation(
        document_id=document_id,
        reviewer_id=reviewer_id,
        comment=evaluation.comment,
        status=evaluation.status,
        created_at=datetime.utcnow()
    )
    db.add(db_eval)
    db.commit()
    db.refresh(db_eval)
    return db_eval

# Get evaluations for a document
def get_evaluations_for_document(db: Session, document_id: int) -> List[schemas.EvaluationOut]:
    evaluations = db.query(models.DocumentEvaluation).options(
        joinedload(models.DocumentEvaluation.reviewer)
    ).filter(models.DocumentEvaluation.document_id == document_id).all()

    return [
        schemas.EvaluationOut(
            id=eval.id,
            comment=eval.comment,
            status=eval.status,
            reviewer_email=eval.reviewer.email if eval.reviewer else "Unknown Reviewer",
            created_at=eval.created_at
        ) for eval in evaluations
    ]

# Get all users (admin)
def get_all_users(db: Session) -> List[schemas.UserOut]:
    # Eager load any relationships needed for UserOut if applicable (e.g., documents, evaluations)
    # For now, just fetching users directly is fine if UserOut only uses direct columns.
    users = db.query(models.User).all()
    return [schemas.UserOut.from_orm(user) for user in users]

# --- NEW FUNCTION FOR ADMIN FUNCTIONALITY ---
def assign_reviewer_to_document(db: Session, document_id: int, reviewer_id: int) -> Optional[schemas.DocumentOut]:
    """Assigns a reviewer to a specific document."""
    document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not document:
        return None

    # Check if the reviewer_id exists and has the 'reviewer' role (optional but good practice)
    reviewer = db.query(models.User).filter(models.User.id == reviewer_id).first()
    if not reviewer or reviewer.role != "reviewer":
        # You might raise an HTTPException here in the API route instead
        print(f"Error: Reviewer with ID {reviewer_id} not found or is not a reviewer.")
        return None

    document.assigned_reviewer_id = reviewer_id
    db.add(document)
    db.commit()
    db.refresh(document) # Refresh to get the updated assigned_reviewer relationship loaded

    # Now, explicitly load the assigned_reviewer relationship for the refreshed document
    # so that assigned_reviewer_email can be populated correctly.
    document = db.query(models.Document).options(
        joinedload(models.Document.evaluations).joinedload(models.DocumentEvaluation.reviewer),
        joinedload(models.Document.assigned_reviewer)
    ).filter(models.Document.id == document_id).first()

    if document:
        return _map_document_to_document_out(document)
    return None # Should not happen if document was found initially
