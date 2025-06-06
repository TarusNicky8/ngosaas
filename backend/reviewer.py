from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import List, Annotated

# Import core backend modules
from backend import crud, schemas, models
# Import dependencies from the dedicated dependencies module
from backend.dependencies import get_db # CORRECTED: Import get_db from backend.dependencies
# Import role-specific user dependency from auth module
from backend.auth import get_current_reviewer_user # CORRECTED: Import get_current_reviewer_user from backend.auth
from backend.schemas import map_document_model_to_out_schema

router = APIRouter(prefix="/reviewer", tags=["reviewer"])

@router.get("/documents", response_model=List[schemas.DocumentOut])
async def list_documents(
    db: Session = Depends(get_db), # Use get_db from backend.dependencies
    current_user: models.User = Depends(get_current_reviewer_user) # Use dependency from backend.auth
):
    print(f"[REVIEWER DOCS] User: {current_user.id} ({current_user.email}), Role: {current_user.role}")
    documents_models = crud.get_documents_by_reviewer(db, reviewer_id=current_user.id)
    print(f"[REVIEWER DOCS] Found {len(documents_models)} documents for Reviewer ID={current_user.id}")
    return [map_document_model_to_out_schema(doc_model) for doc_model in documents_models]


@router.get("/documents/{doc_id}/download")
async def download_document(
    doc_id: int,
    db: Session = Depends(get_db), # Use get_db from backend.dependencies
    current_user: models.User = Depends(get_current_reviewer_user) # Use dependency from backend.auth
):
    document_model = crud.get_document(db, doc_id)
    if not document_model:
        raise HTTPException(status_code=404, detail="Document not found")

    if not document_model.url:
        raise HTTPException(status_code=500, detail="Document URL not available.")

    return RedirectResponse(url=document_model.url, status_code=status.HTTP_302_FOUND)


@router.post("/documents/{doc_id}/evaluate", response_model=schemas.EvaluationOut)
async def evaluate_document(
    doc_id: int,
    evaluation: schemas.EvaluationCreate,
    db: Session = Depends(get_db), # Use get_db from backend.dependencies
    current_user: models.User = Depends(get_current_reviewer_user) # Use dependency from backend.auth
):
    document_model = crud.get_document(db, doc_id)
    if not document_model:
        raise HTTPException(status_code=404, detail="Document not found")

    db_evaluation = crud.create_evaluation(
        db,
        document_id=doc_id,
        reviewer_id=current_user.id,
        comment=evaluation.comment,
        status=evaluation.status
    )
    return schemas.EvaluationOut.from_orm(db_evaluation)
