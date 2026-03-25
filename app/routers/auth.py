from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserResponse, TokenResponse
from app.auth import hash_password, verify_password, create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# ─── REGISTER ──────────────────────────────────────────────
@router.post("/register", response_model=UserResponse, status_code=201)
def register(user: UserCreate, db: Session = Depends(get_db)):

    # check if email already exists
    existing_email = db.query(User).filter(User.email == user.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # check if username already exists
    existing_username = db.query(User).filter(User.username == user.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    # hash the password before saving — never store plain password
    new_user = User(
        email           = user.email,
        username        = user.username,
        hashed_password = hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# ─── LOGIN ─────────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
def login(credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):

    # find user by username
    user = db.query(User).filter(User.username == credentials.username).first()

    # check user exists and password is correct
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # create JWT token with username inside
    token = create_access_token(data={"sub": user.username})

    return {
        "access_token": token,
        "token_type":   "bearer"
    }