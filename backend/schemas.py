# backend/schemas.py
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
import uuid # Import uuid for potential type hinting, though 'str' is used for API boundary

# Import models for type hinting in the mapping function
from backend import models # Assuming backend is the package root

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class EvaluationCreate(BaseModel):
    comment: str
    status: str

class DocumentCreate(BaseModel):
    title: str
    organization: str
    filename: str
    url: str
    grantee_id: str # CORRECTED: Changed from int to str for UUID compatibility from frontend
    assigned_reviewer_id: Optional[str] = None # CORRECTED: Changed from Optional[int] to Optional[str]

class EvaluationOut(BaseModel):
    id: int
    comment: str
    status: str
    reviewer_email: Optional[str] = None
    created_at: datetime

    class Config: # ADDED: Pydantic v1 Config for ORM mode
        orm_mode = True

class UserOut(BaseModel):
    id: str # Already correct for UUID string representation
    email: EmailStr
    full_name: Optional[str] = None
    role: str

    class Config: # ADDED: Pydantic v1 Config for ORM mode
        orm_mode = True

class DocumentOut(BaseModel):
    id: int
    title: str
    organization: str
    filename: str
    url: str
    uploaded_by: Optional[str] = None
    grantee_id: Optional[str] = None # Already correct for UUID string representation
    assigned_reviewer_id: Optional[str] = None # Already correct for UUID string representation
    assigned_reviewer_email: Optional[str] = None

    evaluations: List[EvaluationOut] = Field(default_factory=list)

    class Config: # ADDED: Pydantic v1 Config for ORM mode
        orm_mode = True

class AssignReviewer(BaseModel):
    reviewer_id: str # Already correct for UUID string representation

# --- HELPER FUNCTION FOR MAPPING MODELS TO SCHEMAS ---
def map_document_model_to_out_schema(doc_model: "models.Document") -> DocumentOut:
    """
    Maps a SQLAlchemy Document model object to a Pydantic DocumentOut schema.
    Handles loading related evaluations and populating derived fields.
    """
    eval_out_list = []
    if doc_model.evaluations:
        for eval_item in doc_model.evaluations:
            eval_out_list.append(EvaluationOut(
                id=eval_item.id,
                comment=eval_item.comment,
                status=eval_item.status,
                reviewer_email=eval_item.reviewer.email if eval_item.reviewer else None,
                created_at=eval_item.created_at
            ))

    return DocumentOut(
        id=doc_model.id,
        title=doc_model.title,
        organization=doc_model.organization,
        filename=doc_model.filename,
        url=doc_model.url,
        uploaded_by=doc_model.uploader.email if doc_model.uploader else None,
        grantee_id=str(doc_model.grantee_id) if doc_model.grantee_id else None, # Ensure this is string conversion
        assigned_reviewer_id=str(doc_model.assigned_reviewer_id) if doc_model.assigned_reviewer_id else None, # Ensure this is string conversion
        assigned_reviewer_email=doc_model.assigned_reviewer_obj.email if doc_model.assigned_reviewer_obj else None,
        evaluations=eval_out_list
    )
