from pydantic import BaseModel, EmailStr
from typing import List, Optional

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

class EvaluationOut(BaseModel):
    reviewer: str
    comment: str
    status: str

    class Config:
        orm_mode = True

class DocumentOut(BaseModel):
    id: int
    title: str
    organization: str
    filename: str
    uploaded_by: str
    url: str
    evaluations: List[EvaluationOut] = []

    class Config:
        orm_mode = True
