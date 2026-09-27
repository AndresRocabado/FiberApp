import os
import secrets
import datetime

import jwt
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

load_dotenv()

router  = APIRouter(prefix="/api/auth", tags=["auth"])
_bearer = HTTPBearer()

# Placeholder values from .env.example / README that must never reach production
_PLACEHOLDERS = {
    "change-me",
    "your_password", "your_password_here",
    "a-long-random-secret-string", "replace-with-a-long-random-string",
}


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value or value in _PLACEHOLDERS:
        raise RuntimeError(f"La variable de entorno {name} es obligatoria (revisa .env)")
    return value


_USERNAME   = _required_env("APP_USERNAME")
_PASSWORD   = _required_env("APP_PASSWORD")
_SECRET     = _required_env("JWT_SECRET")
_EXPIRE_H   = int(os.getenv("JWT_EXPIRE_HOURS", "8"))


class LoginBody(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(body: LoginBody):
    ok_user = secrets.compare_digest(body.username, _USERNAME)
    ok_pass = secrets.compare_digest(body.password, _PASSWORD)
    if not (ok_user and ok_pass):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    exp = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=_EXPIRE_H)
    token = jwt.encode({"sub": body.username, "exp": exp}, _SECRET, algorithm="HS256")
    return {"token": token, "expires_in": _EXPIRE_H * 3600}


def require_auth(creds: HTTPAuthorizationCredentials = Depends(_bearer)) -> str:
    try:
        payload = jwt.decode(creds.credentials, _SECRET, algorithms=["HS256"])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Sesión expirada")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
