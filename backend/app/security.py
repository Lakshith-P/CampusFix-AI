"""Small dependency-light JWT and password helpers for local/demo deployment.
Uses stdlib PBKDF2-HMAC and HMAC-SHA256 JWT signing; change SECRET_KEY before deployment.
"""
from datetime import datetime, timedelta, timezone
import base64, hashlib, hmac, json, os
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db
from .models import User

bearer = HTTPBearer(auto_error=False)
_ITERATIONS = 310_000

def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    return f"pbkdf2_sha256${_ITERATIONS}${_b64(salt)}${_b64(digest)}"

def verify_password(password: str, hashed: str) -> bool:
    try:
        scheme, iterations, salt, expected = hashed.split("$", 3)
        if scheme != "pbkdf2_sha256": return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), _unb64(salt), int(iterations))
        return hmac.compare_digest(actual, _unb64(expected))
    except Exception:
        return False

def create_access_token(user_id: int) -> str:
    header = _b64(json.dumps({"alg":"HS256","typ":"JWT"}, separators=(",",":")).encode())
    payload = _b64(json.dumps({"sub":str(user_id),"exp":int((datetime.now(timezone.utc)+timedelta(minutes=settings.access_token_minutes)).timestamp())}, separators=(",",":")).encode())
    body = f"{header}.{payload}"
    signature = _b64(hmac.new(settings.secret_key.encode(), body.encode(), hashlib.sha256).digest())
    return f"{body}.{signature}"

def _decode_token(token: str) -> int:
    try:
        header, payload, signature = token.split(".")
        body = f"{header}.{payload}"
        expected = _b64(hmac.new(settings.secret_key.encode(), body.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected): raise ValueError("signature")
        claims = json.loads(_unb64(payload))
        if int(claims["exp"]) <= int(datetime.now(timezone.utc).timestamp()): raise ValueError("expired")
        return int(claims["sub"])
    except Exception as exc:
        raise HTTPException(401, "Invalid or expired token") from exc

def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)) -> User:
    if credentials is None:
        raise HTTPException(401, "Not authenticated", headers={"WWW-Authenticate":"Bearer"})
    user = db.get(User, _decode_token(credentials.credentials))
    if not user or not user.active: raise HTTPException(401, "Invalid or inactive account")
    return user

def require_roles(*roles: str):
    def checker(user: User = Depends(get_current_user)):
        if user.role not in roles: raise HTTPException(403, "You are not authorized for this action")
        return user
    return checker
