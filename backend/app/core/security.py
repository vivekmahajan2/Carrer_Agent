from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union
import base64
import hashlib
import bcrypt
import jwt
from cryptography.fernet import Fernet
from backend.app.core.config import get_settings

settings = get_settings()


def get_encryption_key() -> bytes:
    """Derive consistent 32-byte urlsafe base64 key from settings.SECRET_KEY."""
    raw_key = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(raw_key)


def encrypt_secret(plain_text: str) -> str:
    """Encrypt sensitive OAuth tokens and secrets."""
    if not plain_text:
        return ""
    f = Fernet(get_encryption_key())
    return f.encrypt(plain_text.encode("utf-8")).decode("utf-8")


def decrypt_secret(cipher_text: str) -> str:
    """Decrypt sensitive OAuth tokens and secrets."""
    if not cipher_text:
        return ""
    f = Fernet(get_encryption_key())
    return f.decrypt(cipher_text.encode("utf-8")).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except (jwt.PyJWTError, Exception):
        return None

