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

    # --- UPDATED FOR PYDANTIC V2 ---
    model_config = {
        "from_attributes": True
    }
    # -------------------------------

class UserOut(BaseModel):
    id: int
    email: EmailStr # Changed to EmailStr for consistency
    full_name: Optional[str] = None
    role: str

    # --- UPDATED FOR PYDANTIC V2 ---
    model_config = {
        "from_attributes": True
    }
    # -------------------------------

class DocumentOut(BaseModel):
    id: int
    title: str
    organization: str
    filename: str
    uploaded_by: Optional[str] = None # Made optional for consistency
    url: Optional[str] = None # Made optional for consistency
    grantee_id: Optional[int] = None # Already made optional
    assigned_reviewer_id: Optional[int] = None
    assigned_reviewer_email: Optional[str] = None

    evaluations: List[EvaluationOut] = []

    # --- UPDATED FOR PYDANTIC V2 ---
    model_config = {
        "from_attributes": True
    }
    # -------------------------------

class DocumentEvaluationOut(BaseModel):
    id: int
    document_id: int
    reviewer_id: int
    comment: str
    status: str
    created_at: datetime

    # --- UPDATED FOR PYDANTIC V2 ---
    model_config = {
        "from_attributes": True
    }
    # -------------------------------

class AssignReviewer(BaseModel):
    """Schema for assigning a reviewer to a document."""
    reviewer_id: int
