# backend/admin.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Annotated

# Import core backend modules
from backend import crud, schemas, models
# Import dependencies from the dedicated dependencies module
from backend.dependencies import get_db # CORRECTED: Import get_db from backend.dependencies
# Import role-specific user dependency from auth module
from backend.auth import get_current_admin_user # CORRECTED: Import get_current_admin_user from backend.auth
from backend.schemas import map_document_model_to_out_schema

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/users", response_model=List[schemas.UserOut])
async def list_users(
    db: Session = Depends(get_db), # Use get_db from backend.dependencies
    current_admin: models.User = Depends(get_current_admin_user) # Use dependency from backend.auth
):
    """
    Retrieves a list of all users in the system.
    Accessible only by admin users.
    """
    print(f"[ADMIN] User: {current_admin.id} ({current_admin.email}), Role: {current_admin.role} is listing all users.")
    users_models = crud.get_all_users(db)
    print(f"[ADMIN] Found {len(users_models)} users.")
    return [schemas.UserOut.from_orm(user_model) for user_model in users_models]

@router.get("/documents", response_model=List[schemas.DocumentOut])
async def list_all_documents(
    db: Session = Depends(get_db), # Use get_db from backend.dependencies
    current_admin: models.User = Depends(get_current_admin_user) # Use dependency from backend.auth
):
    """
    Retrieves a list of all documents in the system, including their evaluations and assigned reviewers.
    Accessible only by admin users.
    """
    print(f"[ADMIN] User: {current_admin.id} ({current_admin.email}), Role: {current_admin.role} is listing all documents.")
    documents_models = crud.get_all_documents(db)
    print(f"[ADMIN] Found {len(documents_models)} documents.")
    return [map_document_model_to_out_schema(doc_model) for doc_model in documents_models]

@router.post("/documents/{doc_id}/assign-reviewer", response_model=schemas.DocumentOut)
async def assign_reviewer_to_document_api(
    doc_id: int,
    assignment: schemas.AssignReviewer,
    db: Session = Depends(get_db), # Use get_db from backend.dependencies
    current_admin: models.User = Depends(get_current_admin_user) # Use dependency from backend.auth
):
    """
    Assigns a reviewer to a specific document.
    Accessible only by admin users.
    """
    print(f"[ADMIN] User: {current_admin.id} ({current_admin.email}), Role: {current_admin.role} is assigning reviewer {assignment.reviewer_id} to document {doc_id}.")

    db_document_model = crud.assign_reviewer_to_document(db, document_id=doc_id, reviewer_id=assignment.reviewer_id)

    if not db_document_model:
        existing_document_model = crud.get_document(db, doc_id)
        if not existing_document_model:
            raise HTTPException(status_code=404, detail="Document not found.")
        
        raise HTTPException(status_code=400, detail="Failed to assign reviewer. Reviewer might not exist or not have 'reviewer' role.")

    print(f"[ADMIN] Reviewer {assignment.reviewer_id} assigned to Document {doc_id} successfully.")
    return map_document_model_to_out_schema(db_document_model)
