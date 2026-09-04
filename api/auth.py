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

_USERNAME   = os.getenv("APP_USERNAME", "admin")
_PASSWORD   = os.getenv("APP_PASSWORD", "admin123")
_SECRET     = os.getenv("JWT_SECRET", "change-me")
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
    exp = datetime.datetime.utcnow() + datetime.timedelta(hours=_EXPIRE_H)
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
