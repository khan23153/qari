"""JWT verification and Firebase token exchange."""
import firebase_admin
from firebase_admin import auth as firebase_auth
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.core.config import settings

_firebase_app = None


def _init_firebase():
    global _firebase_app
    if _firebase_app is None and settings.FIREBASE_CREDENTIALS_PATH:
        _firebase_app = firebase_admin.initialize_app(
            firebase_admin.credentials.Certificate(
                settings.FIREBASE_CREDENTIALS_PATH
            )
        )


async def verify_firebase_token(id_token: str) -> Optional[dict]:
    """Verify a Firebase ID token and return the decoded claims."""
    _init_firebase()
    try:
        decoded = firebase_auth.verify_id_token(id_token)
        return decoded
    except Exception:
        return None


def create_backend_jwt(firebase_uid: str) -> str:
    """Exchange a Firebase UID for a backend JWT."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": firebase_uid,
        "iat": now,
        "exp": now + timedelta(days=30),
        "iss": "qari-core-api",
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_backend_jwt(token: str) -> Optional[dict]:
    """Decode and verify a backend JWT."""
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            issuer="qari-core-api",
        )
    except JWTError:
        return None
