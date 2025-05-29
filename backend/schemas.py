# schemas.py
from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import List, Optional # Ensure Optional is imported

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class EvaluationCreate(BaseModel):
    comment: str
    status: str

class DocumentEvaluationCreate(BaseModel):
    comment: str
    status: str

class EvaluationOut(BaseModel):
    id: int
    comment: str
    status: str
    reviewer_email: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True

class UserOut(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    role: str

    # --- IMPORTANT CHANGE HERE ---
    # Changed from model_config (Pydantic v2) to class Config (Pydantic v1)
    class Config:
        orm_mode = True
    # ----------------------------

class DocumentOut(BaseModel):
    id: int
    title: str
    organization: str
    filename: str
    uploaded_by: Optional[str] = None
    url: Optional[str] = None
    grantee_id: Optional[int] = None
    assigned_reviewer_id: Optional[int] = None
    assigned_reviewer_email: Optional[str] = None

    evaluations: List[EvaluationOut] = []

    class Config:
        orm_mode = True

class DocumentEvaluationOut(BaseModel):
    id: int
    document_id: int
    reviewer_id: int
    comment: str
    status: str
    created_at: datetime

    class Config:
        orm_mode = True

# --- NEW SCHEMAS FOR ADMIN FUNCTIONALITY ---

class AssignReviewer(BaseModel):
    """Schema for assigning a reviewer to a document."""
    reviewer_id: int
