from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse # Use RedirectResponse for Supabase URLs
from sqlalchemy.orm import Session
from typing import List, Annotated # Import Annotated

from backend import crud, schemas, models, dependencies
from backend.schemas import map_document_model_to_out_schema # Import the mapping helper

router = APIRouter(prefix="/reviewer", tags=["reviewer"])

# DOCUMENTS_DIR is no longer needed if using Supabase Storage
# DOCUMENTS_DIR = "uploaded_documents"

# Dependency to get current reviewer user (from main.py or common dependencies)
async def get_current_reviewer_user(current_user: Annotated[models.User, Depends(dependencies.get_current_active_user)]):
    if current_user.role != "reviewer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform this action. Reviewer role required."
        )
    return current_user

@router.get("/documents", response_model=List[schemas.DocumentOut])
async def list_documents(
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(get_current_reviewer_user) # Use the specific reviewer dependency
):
    print(f"[REVIEWER DOCS] User: {current_user.id} ({current_user.email}), Role: {current_user.role}")
    documents_models = crud.get_documents_by_reviewer(db, reviewer_id=current_user.id)
    print(f"[REVIEWER DOCS] Found {len(documents_models)} documents for Reviewer ID={current_user.id}")
    # Map the list of models to list of Pydantic schemas
    return [map_document_model_to_out_schema(doc_model) for doc_model in documents_models]


@router.get("/documents/{doc_id}/download")
async def download_document(
    doc_id: int,
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(get_current_reviewer_user) # Use the specific reviewer dependency
):
    # No authorization check needed here if get_current_reviewer_user already handles it.
    # However, you might want to ensure this reviewer is assigned to this document,
    # or that it's a public document if you allow broader access.
    # For now, assuming reviewer can download any document they have access to via UI.

    document_model = crud.get_document(db, doc_id) # crud.get_document returns models.Document
    if not document_model:
        raise HTTPException(status_code=404, detail="Document not found")

    # For Supabase, we redirect to the public URL
    if not document_model.url:
        raise HTTPException(status_code=500, detail="Document URL not available.")

    # Redirect the client to the Supabase public URL for download
    return RedirectResponse(url=document_model.url, status_code=status.HTTP_302_FOUND)


@router.post("/documents/{doc_id}/evaluate", response_model=schemas.EvaluationOut)
async def evaluate_document(
    doc_id: int,
    evaluation: schemas.EvaluationCreate, # <--- CORRECTED SCHEMA NAME
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(get_current_reviewer_user) # Use the specific reviewer dependency
):
    # No authorization check needed here if get_current_reviewer_user already handles it.

    document_model = crud.get_document(db, doc_id) # Get the document to ensure it exists
    if not document_model:
        raise HTTPException(status_code=404, detail="Document not found")

    # Ensure the reviewer is assigned to this document if that's a business rule
    # if document_model.assigned_reviewer_id != current_user.id:
    #     raise HTTPException(status_code=403, detail="You are not assigned to review this document.")

    db_evaluation = crud.create_evaluation(
        db,
        document_id=doc_id,
        reviewer_id=current_user.id,
        comment=evaluation.comment, # Pass comment explicitly
        status=evaluation.status # Pass status explicitly
    )
    # Convert the returned model to the Pydantic schema for the response
    return schemas.EvaluationOut.from_orm(db_evaluation)
