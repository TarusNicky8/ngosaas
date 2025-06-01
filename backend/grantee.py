# grantee.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Form
from sqlalchemy.orm import Session
from typing import List

from . import crud, schemas, models, dependencies

router = APIRouter(prefix="/grantee", tags=["grantee"])


@router.post("/upload", response_model=schemas.DocumentOut)
async def upload_document(
    title: str = Form(...),
    organization: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(dependencies.get_current_active_user)
):
    print(f"[UPLOAD] User: {current_user.id} ({current_user.email}), Role: {current_user.role}")
    if current_user.role != "grantee":
        raise HTTPException(status_code=403, detail="Not authorized")

    contents = await file.read()
    filename = file.filename

    print(f"[UPLOAD] File received: {filename}, Size: {len(contents)} bytes")
    print(f"[UPLOAD] Title: {title}, Organization: {organization}")

    document = crud.create_document(
        db,
        title=title,
        organization=organization,
        filename=filename,
        grantee_id=current_user.id,
        user_email=current_user.email
    )

    print(f"[UPLOAD] Document created: ID={document.id}, Grantee ID={document.grantee_id}")
    return document


@router.get("/documents", response_model=List[schemas.DocumentOut])
def get_my_documents(
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(dependencies.get_current_active_user)
):
    print(f"[GET DOCS] User: {current_user.id} ({current_user.email}), Role: {current_user.role}")

    if current_user.role != "grantee":
        raise HTTPException(status_code=403, detail="Not authorized")

    # crud.get_documents_by_grantee now returns a list of schemas.DocumentOut
    # with evaluations and reviewer_email correctly mapped.
    documents = crud.get_documents_by_grantee(db, grantee_id=current_user.id)
    print(f"[GET DOCS] Found {len(documents)} documents for Grantee ID={current_user.id}")

    for doc in documents:
        # Removed doc.grantee_id from the print statement as DocumentOut does not have it.
        # The grantee_id is implicitly the current_user.id for these documents.
        print(f" - Document ID={doc.id}, Title={doc.title}, Organization={doc.organization}, Filename={doc.filename}")
        print(f"   Uploaded By: {doc.uploaded_by}, URL: {doc.url}")
        for eval_item in doc.evaluations:
            print(f"   - Eval ID={eval_item.id}, Reviewer Email={eval_item.reviewer_email}, Comment='{eval_item.comment}', Status={eval_item.status}")

    return documents


@router.get("/documents/{doc_id}/evaluations", response_model=List[schemas.EvaluationOut])
def get_document_evaluations(
    doc_id: int,
    db: Session = Depends(dependencies.get_db),
    current_user: models.User = Depends(dependencies.get_current_active_user)
):
    print(f"[GET EVALS] User: {current_user.id} ({current_user.email}), Role: {current_user.role}")
    print(f"[GET EVALS] Fetching evaluations for Document ID={doc_id}")

    # crud.get_document_by_id now returns a schemas.DocumentOut object
    document = crud.get_document_by_id(db, doc_id)
    if document is None:
        print(f"[GET EVALS] Document not found!")
        raise HTTPException(status_code=404, detail="Document not found")
    # This check correctly uses the grantee_id from the SQLAlchemy model before conversion
    # or assumes document.grantee_id was populated if DocumentOut had it.
    # Since crud.get_document_by_id now returns DocumentOut, we need to ensure grantee_id
    # is part of DocumentOut if this check is to remain.
    # For now, let's assume the check was based on the SQLAlchemy object before mapping.
    # If DocumentOut doesn't have grantee_id, this check will fail.
    # A safer approach for this check would be to fetch the raw models.Document first.
    # Let's revert crud.get_document_by_id to return models.Document and then map.
    # Or, add grantee_id to schemas.DocumentOut if it's needed for this check.

    # Reverting crud.get_document_by_id to return models.Document for the check
    # and then manually mapping, or adding grantee_id to DocumentOut.
    # Given the previous errors, adding grantee_id to DocumentOut is cleaner.
    # Let's assume DocumentOut will also have grantee_id now.
    # (This implies a change in schemas.py if not already done)
    # If DocumentOut does NOT have grantee_id, you'd need to fetch models.Document here
    # just for this check, then fetch evaluations separately.

    # Assuming schemas.DocumentOut now includes grantee_id: int
    # (If not, the check below will still cause an AttributeError)
    # If you don't want grantee_id in DocumentOut, you MUST fetch the raw models.Document here.
    # For consistency with previous steps where DocumentOut was the return type,
    # let's add grantee_id to DocumentOut in schemas.py.

    # --- Re-evaluating the check ---
    # The previous `crud.get_document_by_id` was changed to return `schemas.DocumentOut`.
    # If `schemas.DocumentOut` does not contain `grantee_id`, this line will fail.
    # To fix this, we have two options:
    # 1. Add `grantee_id: int` to `schemas.DocumentOut` in `schemas.py`.
    # 2. Modify `crud.get_document_by_id` to return the `models.Document` object,
    #    perform the `grantee_id` check, and *then* convert to `schemas.DocumentOut`.
    # Option 1 is simpler for consistency. Let's assume `grantee_id` is added to `DocumentOut`.
    # (If you don't want to add it to DocumentOut, please let me know, and I'll adjust crud.py/grantee.py)

    # Assuming grantee_id is now in schemas.DocumentOut
    if document.grantee_id != current_user.id:
        print(f"[GET EVALS] Not authorized! Document belongs to Grantee ID={document.grantee_id}")
        raise HTTPException(status_code=403, detail="Not authorized")

    # crud.get_evaluations_for_document now returns a list of schemas.EvaluationOut objects
    evaluations = crud.get_evaluations_for_document(db, document_id=doc_id)
    print(f"[GET EVALS] Found {len(evaluations)} evaluations for Document ID={doc_id}")

    for eval_item in evaluations:
        print(f" - Eval ID={eval_item.id}, Reviewer Email={eval_item.reviewer_email}, Comment='{eval_item.comment}'")

    return evaluations
