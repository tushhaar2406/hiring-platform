from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM  = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

# bcrypt handles password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ─── Password helpers ──────────────────────────────────────

def hash_password(password: str) -> str:
    # converts "mypassword123" → "$2b$12$randomhash..."
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # checks if plain password matches the stored hash
    return pwd_context.verify(plain_password, hashed_password)

# ─── Token helpers ─────────────────────────────────────────

def create_access_token(data: dict) -> str:
    to_encode = data.copy()

    # token expires after 30 minutes
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    # encode everything into a JWT string
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_token(token: str) -> str:
    try:
        # decode the token and extract username
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except JWTError:
        return None