import jwt
import sqlite3
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from database import get_db

SECRET_KEY = "change-this-in-production"
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def hash_password(password: str) -> str:
    """
    Hashes a plain text password using the configured password context.
    """
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """
    Verifies a plain text password against a given hashed password.
    """
    return pwd_context.verify(password, hashed)


def create_token(data: dict) -> str:
    """
    Creates a JWT token encoding the provided data with an expiration time.
    """
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(
        minutes=TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: sqlite3.Connection = Depends(get_db),
):
    """
    Retrieves the user from the database based on the provided JWT token.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc

    user = db.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
