# backend/grantee.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Form
from sqlalchemy.orm import Session
from typing import List, Annotated

# Import core backend modules
from backend import crud, schemas, models
# Import dependencies from the dedicated dependencies module
from backend.dependencies import get_db # CORRECTED: Import get_db from backend.dependencies
# Import role-specific user dependency from auth module
from backend.auth import get_current_grantee_user # CORRECTED: Import get_current_grantee_user from backend.auth
from backend.schemas import map_document_model_to_out_schema # Import the mapping helper

router = APIRouter(prefix="/grantee", tags=["grantee"])

# The /upload endpoint in main.py handles file uploads.
# This endpoint is kept here as a placeholder if you need to use a router
# for uploads in the future, but it's currently set to raise an error
# to indicate that main.py's endpoint should be used.
@router.post("/upload", response_model=schemas.DocumentOut)
async def upload_document(
    title: str = Form(...),
    organization: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db), # Use get_db from backend.dependencies
    current_user: models.User = Depends(get_current_grantee_user) # Use dependency from backend.auth
):
    print(f"[UPLOAD] User: {current_user.id} ({current_user.email}), Role: {current_user.role}")
    raise HTTPException(status_code=405, detail="Please use the /grantee/upload endpoint in main.py for file uploads.")


@router.get("/documents", response_model=List[schemas.DocumentOut])
async def get_my_documents(
    db: Session = Depends(get_db), # Use get_db from backend.dependencies
    current_user: models.User = Depends(get_current_grantee_user) # Use dependency from backend.auth
):
    print(f"[GET DOCS] User: {current_user.id} ({current_user.email}), Role: {current_user.role}")

    documents_models = crud.get_documents_by_grantee(db, grantee_id=current_user.id)
    print(f"[GET DOCS] Found {len(documents_models)} documents for Grantee ID={current_user.id}")

    return [map_document_model_to_out_schema(doc_model) for doc_model in documents_models]


@router.get("/documents/{doc_id}/evaluations", response_model=List[schemas.EvaluationOut])
async def get_document_evaluations(
    doc_id: int,
    db: Session = Depends(get_db), # Use get_db from backend.dependencies
    current_user: models.User = Depends(get_current_grantee_user) # Use dependency from backend.auth
):
    print(f"[GET EVALS] User: {current_user.id} ({current_user.email}), Role: {current_user.role}")
    print(f"[GET EVALS] Fetching evaluations for Document ID={doc_id}")

    document_model = crud.get_document(db, doc_id)
    if document_model is None:
        print(f"[GET EVALS] Document not found!")
        raise HTTPException(status_code=404, detail="Document not found")

    if document_model.grantee_id != current_user.id:
        print(f"[GET EVALS] Not authorized! Document belongs to Grantee ID={document_model.grantee_id}")
        raise HTTPException(status_code=403, detail="Not authorized to view evaluations for this document.")

    evaluations_models = crud.get_evaluations_for_document(db, document_id=doc_id)
    print(f"[GET EVALS] Found {len(evaluations_models)} evaluations for Document ID={doc_id}")

    return [schemas.EvaluationOut.from_orm(eval_model) for eval_model in evaluations_models]
