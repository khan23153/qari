"""Security: Firebase token verification, password hashing, and backend JWT creation/verification."""

import hashlib
import hmac
import json
import os
import time
from typing import Any, Optional

import firebase_admin
from firebase_admin import auth as firebase_auth
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_firebase_app: Optional[firebase_admin.App] = None


def init_firebase() -> None:
    """Initialise the Firebase Admin SDK from env-provided credentials."""
    global _firebase_app
    if _firebase_app is not None:
        return

    cred_json = settings.firebase_credentials_json
    project_id = settings.firebase_project_id

    if cred_json:
        try:
            cred_dict = json.loads(cred_json)
            cred = firebase_admin.credentials.Certificate(cred_dict)
            _firebase_app = firebase_admin.initialize_app(cred, name="qari")
            logger.info("firebase.initialised", project_id=cred_dict.get("project_id"))
            return
        except Exception as exc:
            logger.error("firebase.init_failed", error=str(exc))

    # Fallback: rely on GOOGLE_APPLICATION_CREDENTIALS env var
    try:
        cred = firebase_admin.credentials.ApplicationDefault()
        opts = {"projectId": project_id} if project_id else {}
        _firebase_app = firebase_admin.initialize_app(cred, name="qari", options=opts)
        logger.info("firebase.initialised_default", project_id=project_id)
    except Exception as exc:
        logger.warning("firebase.not_initialised", error=str(exc))
        _firebase_app = None


def verify_firebase_token(token: str) -> Optional[dict[str, Any]]:
    """Verify a Firebase ID token and return the decoded claims.

    Returns ``None`` if verification fails or Firebase is not configured.
    """
    if _firebase_app is None:
        init_firebase()
    if _firebase_app is None:
        logger.error("firebase.app_not_available")
        return None

    try:
        decoded = firebase_auth.verify_id_token(token, app=_firebase_app)
        return decoded
    except firebase_auth.ExpiredIdTokenError:
        logger.warning("firebase.token_expired")
        return None
    except firebase_auth.InvalidIdTokenError:
        logger.warning("firebase.token_invalid")
        return None
    except Exception as exc:
        logger.error("firebase.verification_error", error=str(exc))
        return None


# ---------------------------------------------------------------------------
# Backend JWT
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Password hashing (PBKDF2-HMAC-SHA256, dependency-free)
# ---------------------------------------------------------------------------

_PBKDF2_ALGO = "pbkdf2_sha256"
_PBKDF2_ITERATIONS = 100_000


def hash_password(plain: str, *, iterations: int = _PBKDF2_ITERATIONS) -> str:
    """Hash a plaintext password and return a self-describing encoded string.

    Format: ``pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>``
    """
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt, iterations)
    return f"{_PBKDF2_ALGO}${iterations}${salt.hex()}${dk.hex()}"


def verify_password(plain: str, stored: Optional[str]) -> bool:
    """Verify *plain* against a stored ``hash_password`` string.

    Uses a constant-time comparison and returns ``False`` on any malformed
    input rather than raising.
    """
    if not stored:
        return False
    try:
        algo, iters_s, salt_hex, hash_hex = stored.split("$")
    except ValueError:
        return False
    if algo != _PBKDF2_ALGO:
        return False
    try:
        iterations = int(iters_s)
        salt = bytes.fromhex(salt_hex)
    except ValueError:
        return False
    dk = hashlib.pbkdf2_hmac("sha256", plain.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(dk.hex(), hash_hex)


class TokenData(BaseModel):
    """Payload embedded in the backend JWT."""
    sub: str          # user UUID
    firebase_uid: str = ""
    email: Optional[str] = None
    exp: int


def create_access_token(
    *,
    user_id: str,
    firebase_uid: str = "",
    email: Optional[str] = None,
) -> str:
    """Create a signed backend JWT for *user_id*."""
    now = int(time.time())
    payload = {
        "sub": user_id,
        "firebase_uid": firebase_uid,
        "email": email,
        "iat": now,
        "exp": now + settings.jwt_access_token_expire_minutes * 60,
        "iss": settings.app_name,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Optional[TokenData]:
    """Decode and verify a backend JWT. Returns ``None`` on failure."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"verify_exp": True},
        )
        return TokenData(
            sub=payload["sub"],
            firebase_uid=payload.get("firebase_uid", ""),
            email=payload.get("email"),
            exp=payload.get("exp", 0),
        )
    except JWTError as exc:
        logger.warning("jwt.decode_failed", error=str(exc))
        return None
    except KeyError as exc:
        logger.warning("jwt.missing_claim", missing=str(exc))
        return None
