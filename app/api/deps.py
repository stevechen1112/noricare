from typing import Generator, Optional

import jwt
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import SessionLocal
from app.models.all_models import AuthAccount

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_account(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> AuthAccount:
    try:
        payload = decode_token(token)
        account_id = payload.get("account_id")
        if not account_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

        account = db.query(AuthAccount).filter(AuthAccount.id == account_id).first()
        if not account:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account not found")
        return account
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# 可選認證：如果有 token 就驗證，沒有就返回 None
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_account_optional(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme_optional),
) -> Optional[AuthAccount]:
    """可選認證：有 token 就驗證，沒有返回 None"""
    if not token:
        return None
    try:
        payload = decode_token(token)
        account_id = payload.get("account_id")
        if not account_id:
            return None
        account = db.query(AuthAccount).filter(AuthAccount.id == account_id).first()
        return account
    except Exception:
        return None
