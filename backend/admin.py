# backend/admin.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Annotated # Import Annotated

from backend import crud, schemas, models, dependencies
from backend.schemas import map_document_model_to_out_schema # Import the mapping helper

router = APIRouter(prefix="/admin", tags=["admin"])

# Dependency to ensure the current user is an admin
async def get_current_admin_user(current_user: Annotated[models.User, Depends(dependencies.get_current_active_user)]):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform this action. Admin role required."
        )
    return current_user

@router.get("/users", response_model=List[schemas.UserOut])
async def list_users( # Changed to async
    db: Session = Depends(dependencies.get_db),
    current_admin: models.User = Depends(get_current_admin_user) # Ensure only admins can access
):
    """
    Retrieves a list of all users in the system.
    Accessible only by admin users.
    """
    print(f"[ADMIN] User: {current_admin.id} ({current_admin.email}), Role: {current_admin.role} is listing all users.")
    users_models = crud.get_all_users(db) # crud returns models.User
    print(f"[ADMIN] Found {len(users_models)} users.")
    # Map the list of models to list of Pydantic schemas
    return [schemas.UserOut.from_orm(user_model) for user_model in users_models]

@router.get("/documents", response_model=List[schemas.DocumentOut])
async def list_all_documents( # Changed to async
    db: Session = Depends(dependencies.get_db),
    current_admin: models.User = Depends(get_current_admin_user) # Ensure only admins can access
):
    """
    Retrieves a list of all documents in the system, including their evaluations and assigned reviewers.
    Accessible only by admin users.
    """
    print(f"[ADMIN] User: {current_admin.id} ({current_admin.email}), Role: {current_admin.role} is listing all documents.")
    documents_models = crud.get_all_documents(db) # crud returns models.Document
    print(f"[ADMIN] Found {len(documents_models)} documents.")
    # Map the list of models to list of Pydantic schemas
    return [map_document_model_to_out_schema(doc_model) for doc_model in documents_models]

@router.post("/documents/{doc_id}/assign-reviewer", response_model=schemas.DocumentOut)
async def assign_reviewer_to_document_api( # Changed to async
    doc_id: int,
    assignment: schemas.AssignReviewer, # Expects a reviewer_id in the request body
    db: Session = Depends(dependencies.get_db),
    current_admin: models.User = Depends(get_current_admin_user) # Ensure only admins can access
):
    """
    Assigns a reviewer to a specific document.
    Accessible only by admin users.
    """
    print(f"[ADMIN] User: {current_admin.id} ({current_admin.email}), Role: {current_admin.role} is assigning reviewer {assignment.reviewer_id} to document {doc_id}.")

    db_document_model = crud.assign_reviewer_to_document(db, document_id=doc_id, reviewer_id=assignment.reviewer_id)

    if not db_document_model:
        # If crud returns None, it implies either doc or reviewer was problematic.
        # We need to distinguish between document not found and reviewer not valid.
        # crud.assign_reviewer_to_document now returns the eager-loaded model or None.
        # Let's check for document existence first for a more specific error.
        existing_document_model = crud.get_document(db, doc_id) # Get raw model for check
        if not existing_document_model:
            raise HTTPException(status_code=404, detail="Document not found.")
        
        # If document exists but assignment failed, it's likely the reviewer ID was invalid
        raise HTTPException(status_code=400, detail="Failed to assign reviewer. Reviewer might not exist or not have 'reviewer' role.")

    print(f"[ADMIN] Reviewer {assignment.reviewer_id} assigned to Document {doc_id} successfully.")
    # Map the returned model to the Pydantic schema for the response
    return map_document_model_to_out_schema(db_document_model)

# You might also add endpoints for:
# - Deleting users
# - Deleting documents
# - Changing user roles (e.g., promote grantee to reviewer)
# - Viewing audit logs (future AI integration point)
