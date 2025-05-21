from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="grantee")

    evaluations = relationship("DocumentEvaluation", back_populates="reviewer")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    organization = Column(String)
    filename = Column(String)
    user_email = Column(String)

    evaluations = relationship("DocumentEvaluation", back_populates="document")


class DocumentEvaluation(Base):
    __tablename__ = "document_evaluations"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    reviewer_id = Column(Integer, ForeignKey("users.id"))
    comment = Column(String)
    status = Column(String)

    document = relationship("Document", back_populates="evaluations")
    reviewer = relationship("User", back_populates="evaluations")
