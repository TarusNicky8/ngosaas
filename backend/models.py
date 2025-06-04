# backend/models.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func # Import func for server_default timestamps
from .database import Base # Assuming Base is imported from your database setup

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True) # New field
    role = Column(String, default="grantee", nullable=False) # 'grantee', 'reviewer', 'admin'
    is_active = Column(Boolean, default=True) # New field
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # New timestamp
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) # New timestamp

    # Relationships
    uploaded_documents = relationship("Document", back_populates="uploader", foreign_keys="[Document.grantee_id]")
    assigned_documents = relationship("Document", back_populates="assigned_reviewer_obj", foreign_keys="[Document.assigned_reviewer_id]")
    evaluations = relationship("Evaluation", back_populates="reviewer") # Renamed from DocumentEvaluation

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    organization = Column(String, nullable=False)
    filename = Column(String, nullable=False) # Stores the unique Supabase Storage path/filename
    url = Column(String, nullable=False) # Stores the Supabase public URL
    grantee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # This will store the ID of the user assigned to review this document
    assigned_reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Nullable for unassigned
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # New timestamp
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) # New timestamp

    # Relationships
    # Link to the User who uploaded this document (the grantee)
    uploader = relationship("User", back_populates="uploaded_documents", foreign_keys=[grantee_id])
    # Relationship to the evaluations for this document
    evaluations = relationship("Evaluation", back_populates="document") # Renamed from DocumentEvaluation
    # NEW RELATIONSHIP for the assigned reviewer
    assigned_reviewer_obj = relationship("User", back_populates="assigned_documents", foreign_keys=[assigned_reviewer_id])


class Evaluation(Base): # Renamed from DocumentEvaluation
    __tablename__ = "evaluations" # Renamed table name

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    comment = Column(String, nullable=False)
    status = Column(String, nullable=False) # e.g., "approved", "needs revision", "rejected"
    created_at = Column(DateTime(timezone=True), server_default=func.now()) # New timestamp
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) # New timestamp

    document = relationship("Document", back_populates="evaluations")
    reviewer = relationship("User", back_populates="evaluations")