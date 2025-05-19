from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from . import models, schemas, utils, auth
from .database import engine, SessionLocal

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI()

# CORS Middleware to allow React frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Update this in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Token extraction scheme (used by Swagger and secure routes)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# Use secret key and algorithm from auth module
SECRET_KEY = auth.SECRET_KEY
ALGORITHM = auth.ALGORITHM

@app.get("/")
def read_root():
    return {"message": "🚀 FastAPI backend is running!"}

@app.post("/register", status_code=201)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    from .models import User
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pw = utils.hash_password(user.password)
    db_user = User(email=user.email, hashed_password=hashed_pw)
    db.add(db_user)
    db.commit()
    return {"message": "User created successfully"}

# Updated login endpoint for OAuth2 compatibility (form data)
@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    from .models import User
    db_user = db.query(User).filter(User.email == form_data.username).first()
    if not db_user or not utils.verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    token = auth.create_access_token({"sub": db_user.email})
    return {"access_token": token, "token_type": "bearer"}

# Protected route example - requires valid JWT token in Authorization header
@app.get("/dashboard")
def get_dashboard(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email: str = payload.get("sub")
        if user_email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return {"message": f"✅ Welcome to your dashboard, {user_email}!"}
