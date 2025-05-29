from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from datetime import datetime
from sqlalchemy.orm import relationship
from .database import Base # Assuming Base is imported from your database setup

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="grantee")

    # Relationship for evaluations where this user is the reviewer
    evaluations = relationship("DocumentEvaluation", back_populates="reviewer")

    # Relationship for documents uploaded by this user (as a grantee)
    # Explicitly specify the foreign key for this relationship
    uploaded_documents = relationship(
        "Document",
        back_populates="grantee",
        foreign_keys="[Document.grantee_id]" # This tells SQLAlchemy to use Document.grantee_id
    )
    # Relationship for documents this user is assigned to review
    # Explicitly specify the foreign key for this relationship
    assigned_documents = relationship(
        "Document",
        back_populates="assigned_reviewer",
        foreign_keys="[Document.assigned_reviewer_id]" # This tells SQLAlchemy to use Document.assigned_reviewer_id
    )


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    organization = Column(String)
    filename = Column(String)
    user_email = Column(String) # This stores the email of the uploader (grantee)
    grantee_id = Column(Integer, ForeignKey("users.id"))
    uploaded_by = Column(String) # To store the name/email of the uploader
    url = Column(String)         # To store the URL for downloading the document

    # NEW COLUMN for reviewer assignment
    # This will store the ID of the user assigned to review this document
    assigned_reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    # Link to the User who uploaded this document (the grantee)
    grantee = relationship("User", back_populates="uploaded_documents", foreign_keys=[grantee_id])
    # Relationship to the evaluations for this document
    evaluations = relationship("DocumentEvaluation", back_populates="document")
    # NEW RELATIONSHIP for the assigned reviewer
    assigned_reviewer = relationship("User", back_populates="assigned_documents", foreign_keys=[assigned_reviewer_id])


class DocumentEvaluation(Base):
    __tablename__ = "document_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    reviewer_id = Column(Integer, ForeignKey("users.id"))
    comment = Column(String)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="evaluations")
    reviewer = relationship("User", back_populates="evaluations")
