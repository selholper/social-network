from datetime import datetime, timedelta
from typing import Any, Union

from bcrypt import gensalt, hashpw, checkpw
from jose import jwt

from app.core.config import settings


def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return checkpw(bytes, hashed_bytes) 


def get_password_hash(password: str) -> str:
    bytes = password.encode('utf-8')
    salt = gensalt()
    return hashpw(bytes, salt).decode('utf-8')
