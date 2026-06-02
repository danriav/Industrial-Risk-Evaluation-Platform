from __future__ import annotations

import secrets

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from .config import settings


security = HTTPBasic()


def require_basic_auth(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    if (
        not settings.basic_auth_username
        or not settings.basic_auth_password
        or settings.basic_auth_password.startswith("CHANGE_ME")
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Basic authentication is not configured",
        )

    username_ok = secrets.compare_digest(credentials.username, settings.basic_auth_username)
    password_ok = secrets.compare_digest(credentials.password, settings.basic_auth_password)
    if not (username_ok and password_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
