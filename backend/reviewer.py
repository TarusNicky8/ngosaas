from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import os

from . import crud, schemas, models, dependencies

router = APIRouter(prefix="/reviewer", tags=["reviewer"])

DOCUMENTS_DIR = "uploaded_documents"  # Adjust this as per your project structure

@router.get("/documents", response_model=List[schemas.DocumentOut])
def list_documents(db: Session = Depends(dependencies.get_db),
                   current_user: models.User = Depends(dependencies.get_current_active_user)):
    if current_user.role != "reviewer":
        raise HTTPException(status_code=403, detail="Not authorized")
    return crud.get_all_documents(db)

@router.get("/documents/{doc_id}/download")
def download_document(doc_id: int, db: Session = Depends(dependencies.get_db),
                      current_user: models.User = Depends(dependencies.get_current_active_user)):
    if current_user.role != "reviewer":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    document = crud.get_document_by_id(db, doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    filepath = os.path.join(DOCUMENTS_DIR, document.filename)
    if not os.path.isfile(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(path=filepath, filename=document.filename, media_type="application/octet-stream")

@router.post("/documents/{doc_id}/evaluate", response_model=schemas.DocumentEvaluationOut)
def evaluate_document(doc_id: int, evaluation: schemas.DocumentEvaluationCreate,
                      db: Session = Depends(dependencies.get_db),
                      current_user: models.User = Depends(dependencies.get_current_active_user)):
    if current_user.role != "reviewer":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    document = crud.get_document_by_id(db, doc_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return crud.create_evaluation(db, document_id=doc_id, reviewer_id=current_user.id, evaluation=evaluation)
