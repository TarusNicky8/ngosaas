# admin.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from . import crud, schemas, models, dependencies # Adjust 'backend' import based on your project structure

router = APIRouter(prefix="/admin", tags=["admin"])

# Dependency to ensure the current user is an admin
def get_current_admin_user(current_user: models.User = Depends(dependencies.get_current_active_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform this action. Admin role required."
        )
    return current_user

@router.get("/users", response_model=List[schemas.UserOut])
def list_users(
    db: Session = Depends(dependencies.get_db),
    current_admin: models.User = Depends(get_current_admin_user) # Ensure only admins can access
):
    """
    Retrieves a list of all users in the system.
    Accessible only by admin users.
    """
    print(f"[ADMIN] User: {current_admin.id} ({current_admin.email}), Role: {current_admin.role} is listing all users.")
    users = crud.get_all_users(db)
    print(f"[ADMIN] Found {len(users)} users.")
    return users

@router.get("/documents", response_model=List[schemas.DocumentOut])
def list_all_documents(
    db: Session = Depends(dependencies.get_db),
    current_admin: models.User = Depends(get_current_admin_user) # Ensure only admins can access
):
    """
    Retrieves a list of all documents in the system, including their evaluations and assigned reviewers.
    Accessible only by admin users.
    """
    print(f"[ADMIN] User: {current_admin.id} ({current_admin.email}), Role: {current_admin.role} is listing all documents.")
    documents = crud.get_all_documents(db)
    print(f"[ADMIN] Found {len(documents)} documents.")
    return documents

@router.post("/documents/{doc_id}/assign-reviewer", response_model=schemas.DocumentOut)
def assign_reviewer_to_document_api(
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

    document = crud.assign_reviewer_to_document(db, document_id=doc_id, reviewer_id=assignment.reviewer_id)

    if not document:
        # The crud function might return None if document or reviewer is not found/valid
        # We need to distinguish between document not found and reviewer not valid
        # For simplicity here, we'll check the document existence first.
        # If the reviewer was invalid, crud.assign_reviewer_to_document would have printed an error.
        # A more robust API would return specific errors for reviewer not found/invalid role.
        # For now, if crud returns None, it implies either doc or reviewer was problematic.
        # Let's re-fetch the document to give a more specific error if needed.
        existing_document = crud.get_document_by_id(db, doc_id)
        if not existing_document:
            raise HTTPException(status_code=404, detail="Document not found.")
        
        # If document exists but assignment failed, it's likely the reviewer ID was invalid
        raise HTTPException(status_code=400, detail="Failed to assign reviewer. Reviewer might not exist or not have 'reviewer' role.")

    print(f"[ADMIN] Reviewer {assignment.reviewer_id} assigned to Document {doc_id} successfully.")
    return document

# You might also add endpoints for:
# - Deleting users
# - Deleting documents
# - Changing user roles (e.g., promote grantee to reviewer)
# - Viewing audit logs (future AI integration point)
