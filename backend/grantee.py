# grantee.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Form
from sqlalchemy.orm import Session
from typing import List, Annotated # Import Annotated

from backend import crud, schemas, models, dependencies
from backend.schemas import map_document_model_to_out_schema # Import the mapping helper

router = APIRouter(prefix="/grantee", tags=["grantee"])

# Dependency to get current grantee user (from main.py or common dependencies)
async def get_current_grantee_user(current_user: Annotated[models.User, Depends(dependencies.get_current_active_user)]):
    if current_user.role != "grantee":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform this action. Grantee role required."
        )
    return current_user

@router.post("/upload", response_model=schemas.DocumentOut)
async def upload_document(
    title: str = Form(...),
    organization: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(get_current_grantee_user) # Use the specific grantee dependency
):
    print(f"[UPLOAD] User: {current_user.id} ({current_user.email}), Role: {current_user.role}")

    # The file upload logic (to Supabase) is now in main.py's upload_file_to_supabase helper
    # We need to call that helper from here.
    # To do this, we need to pass the supabase_client and SUPABASE_STORAGE_BUCKET from main.py
    # This implies either:
    # 1. Moving upload_file_to_supabase into a shared utility or a dependency.
    # 2. Passing the supabase_client as a dependency (more complex setup for routers).
    # 3. For now, let's assume main.py handles the direct upload route,
    #    or we re-implement the upload here if this is the only upload endpoint.
    # Given the structure, the main.py upload_document_route is already handling this.
    # This `grantee.py`'s /upload endpoint seems to be a duplicate or old.
    # Let's remove this duplicate endpoint if main.py already has it.

    # Re-evaluating: The user's main.py already has a /grantee/upload endpoint.
    # This `grantee.py`'s /upload endpoint is redundant and will cause a conflict.
    # It also uses an old `crud.create_document` signature.
    # I will remove this duplicate endpoint from grantee.py.
    raise HTTPException(status_code=405, detail="Please use the /grantee/upload endpoint in main.py for file uploads.")


@router.get("/documents", response_model=List[schemas.DocumentOut])
async def get_my_documents( # Changed to async
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(get_current_grantee_user) # Use the specific grantee dependency
):
    print(f"[GET DOCS] User: {current_user.id} ({current_user.email}), Role: {current_user.role}")

    documents_models = crud.get_documents_by_grantee(db, grantee_id=current_user.id)
    print(f"[GET DOCS] Found {len(documents_models)} documents for Grantee ID={current_user.id}")

    # Map the list of models to list of Pydantic schemas
    return [map_document_model_to_out_schema(doc_model) for doc_model in documents_models]


@router.get("/documents/{doc_id}/evaluations", response_model=List[schemas.EvaluationOut])
async def get_document_evaluations( # Changed to async
    doc_id: int,
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(get_current_grantee_user) # Use the specific grantee dependency
):
    print(f"[GET EVALS] User: {current_user.id} ({current_user.email}), Role: {current_user.role}")
    print(f"[GET EVALS] Fetching evaluations for Document ID={doc_id}")

    # Fetch the raw models.Document for the authorization check
    document_model = crud.get_document(db, doc_id)
    if document_model is None:
        print(f"[GET EVALS] Document not found!")
        raise HTTPException(status_code=404, detail="Document not found")

    # Check if the document belongs to the current grantee
    if document_model.grantee_id != current_user.id:
        print(f"[GET EVALS] Not authorized! Document belongs to Grantee ID={document_model.grantee_id}")
        raise HTTPException(status_code=403, detail="Not authorized to view evaluations for this document.")

    evaluations_models = crud.get_evaluations_for_document(db, document_id=doc_id)
    print(f"[GET EVALS] Found {len(evaluations_models)} evaluations for Document ID={doc_id}")

    # Map the list of models to list of Pydantic schemas
    return [schemas.EvaluationOut.from_orm(eval_model) for eval_model in evaluations_models]
