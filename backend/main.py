from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from jose import JWTError, jwt
import os
from uuid import uuid4

from . import models, schemas, utils, auth
from .database import engine, SessionLocal

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
SECRET_KEY = auth.SECRET_KEY
ALGORITHM = auth.ALGORITHM
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Serve static files publicly under /uploads
app.mount("/uploads", StaticFiles(directory=UPLOAD_FOLDER), name="uploads")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

@app.get("/")
def read_root():
    return {"message": "🚀 FastAPI backend is running!"}

@app.post("/register", status_code=201)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pw = utils.hash_password(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_pw, role=user.role)
    db.add(db_user)
    db.commit()
    return {"message": "User created successfully"}

@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not utils.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token_data = {"sub": user.email, "role": user.role}
    access_token = auth.create_access_token(data=token_data)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/dashboard")
def get_dashboard(current_user: models.User = Depends(get_current_user)):
    return {
        "message": f"✅ Welcome to your dashboard, {current_user.email}!",
        "role": current_user.role
    }

@app.post("/upload-doc")
async def upload_document(
    title: str = Form(...),
    organization: str = Form(...),
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ext = file.filename.split('.')[-1]
    filename = f"{uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    with open(filepath, "wb") as f:
        f.write(await file.read())

    doc = models.Document(
        title=title,
        organization=organization,
        filename=filename,
        user_email=current_user.email
    )
    db.add(doc)
    db.commit()
    return {"message": "✅ Document uploaded successfully."}

@app.get("/documents")
def list_documents(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "reviewer":
        raise HTTPException(status_code=403, detail="Access denied")
    documents = db.query(models.Document).all()
    result = []
    for doc in documents:
        evals = [
            {
                "reviewer": e.reviewer.email,
                "comment": e.comment,
                "status": e.status,
            }
            for e in doc.evaluations
        ]
        result.append({
            "id": doc.id,
            "title": doc.title,
            "organization": doc.organization,
            "filename": doc.filename,
            "uploaded_by": doc.user_email,
            "url": f"http://localhost:8000/uploads/{doc.filename}",
            "evaluations": evals,
        })
    return result

@app.post("/documents/{doc_id}/evaluate")
def evaluate_document(
    doc_id: int,
    evaluation: schemas.EvaluationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role != "reviewer":
        raise HTTPException(status_code=403, detail="Only reviewers can evaluate")

    existing = db.query(models.DocumentEvaluation).filter_by(
        document_id=doc_id, reviewer_id=current_user.id
    ).first()
    if existing:
        existing.comment = evaluation.comment
        existing.status = evaluation.status
    else:
        eval = models.DocumentEvaluation(
            document_id=doc_id,
            reviewer_id=current_user.id,
            comment=evaluation.comment,
            status=evaluation.status,
        )
        db.add(eval)
    db.commit()
    return {"message": "Evaluation saved"}
