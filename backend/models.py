# backend/models.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID # Import UUID for PostgreSQL UUID type
import uuid # Import uuid for default generation if needed, though sa.text('gen_random_uuid()') is also good

from .database import Base

class User(Base):
    __tablename__ = "users"

    # Changed to UUID for compatibility with Supabase auth.uid() and PostgreSQL UUID type
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4) # Using Python's uuid.uuid4 for client-side generation
    # Alternatively, for database-side generation, you could use:
    # id = Column(UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(String, default="grantee", nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    uploaded_documents = relationship("Document", back_populates="uploader", foreign_keys="[Document.grantee_id]")
    assigned_documents = relationship("Document", back_populates="assigned_reviewer_obj", foreign_keys="[Document.assigned_reviewer_id]")
    evaluations = relationship("Evaluation", back_populates="reviewer")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True) # Document ID can remain integer if needed
    title = Column(String, index=True, nullable=False)
    organization = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    url = Column(String, nullable=False)
    # Changed ForeignKey to UUID to match User.id
    grantee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assigned_reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    uploader = relationship("User", back_populates="uploaded_documents", foreign_keys=[grantee_id])
    evaluations = relationship("Evaluation", back_populates="document")
    assigned_reviewer_obj = relationship("User", back_populates="assigned_documents", foreign_keys=[assigned_reviewer_id])


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True) # Evaluation ID can remain integer
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    # Changed ForeignKey to UUID to match User.id
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    comment = Column(String, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    document = relationship("Document", back_populates="evaluations")
    reviewer = relationship("User", back_populates="evaluations")
