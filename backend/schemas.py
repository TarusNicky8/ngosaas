# backend/schemas.py
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field # Import Field for default_factory
from typing import List, Optional # Ensure Optional is imported

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str
    full_name: Optional[str] = None # Added full_name based on models.py

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class EvaluationCreate(BaseModel):
    comment: str
    status: str

# --- NEW SCHEMA FOR DOCUMENT CREATION WITH SUPABASE DETAILS ---
class DocumentCreate(BaseModel):
    title: str
    organization: str
    filename: str # This will be the Supabase Storage path/filename
    url: str      # This will be the Supabase public URL
    grantee_id: int
    assigned_reviewer_id: Optional[int] = None
# -------------------------------------------------------------

class EvaluationOut(BaseModel):
    id: int
    comment: str
    status: str
    reviewer_email: Optional[str] = None
    created_at: datetime

    # --- PYDANTIC V2 SYNTAX ---
    model_config = {
        "from_attributes": True
    }
    # --------------------------

class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None # Added full_name
    role: str

    # --- PYDANTIC V2 SYNTAX ---
    model_config = {
        "from_attributes": True
    }
    # --------------------------

class DocumentOut(BaseModel):
    id: int
    title: str
    organization: str
    filename: str
    url: str # DocumentOut now expects a URL (non-optional as per new model)
    uploaded_by: Optional[str] = None # This field is from your old model/logic, ensure it's populated
    grantee_id: Optional[int] = None # Still optional if not always populated by ORM
    assigned_reviewer_id: Optional[int] = None
    assigned_reviewer_email: Optional[str] = None

    evaluations: List[EvaluationOut] = Field(default_factory=list) # Use Field for default_factory

    # --- PYDANTIC V2 SYNTAX ---
    model_config = {
        "from_attributes": True
    }
    # --------------------------

class DocumentEvaluationOut(BaseModel): # This schema seems redundant if EvaluationOut is used.
                                        # If you use EvaluationOut for all evaluation responses,
                                        # you can remove this schema.
    id: int
    document_id: int
    reviewer_id: int
    comment: str
    status: str
    created_at: datetime

    # --- PYDANTIC V2 SYNTAX ---
    model_config = {
        "from_attributes": True
    }
    # --------------------------

class AssignReviewer(BaseModel):
    """Schema for assigning a reviewer to a document."""
    reviewer_id: int