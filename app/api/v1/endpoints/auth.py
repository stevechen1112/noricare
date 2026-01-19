"""認證相關 API 端點 (email+password, JWT)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core.security import create_access_token, hash_password, verify_password
from app.models.all_models import AuthAccount, User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserMe


router = APIRouter()


def _get_account_by_email(db: Session, email: str) -> AuthAccount | None:
    return db.query(AuthAccount).filter(AuthAccount.email == email.lower()).first()


@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest, db: Session = Depends(deps.get_db)):
    email = request.email.lower()
    existing = _get_account_by_email(db, email)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="此 Email 已被註冊")

    profile = User(name=request.name)
    db.add(profile)
    db.flush()

    account = AuthAccount(
        email=email,
        name=request.name,
        password_hash=hash_password(request.password),
        user_id=profile.id,
    )
    db.add(account)
    db.commit()
    db.refresh(account)

    token = create_access_token(
        {
            "account_id": account.id,
            "email": account.email,
            "name": account.name,
            "user_id": account.user_id,
        }
    )
    return TokenResponse(
        access_token=token,
        token=token,
        user=UserMe(
            account_id=account.id,
            id=account.user_id,
            email=account.email,
            name=account.name,
            user_id=account.user_id,
        ),
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(deps.get_db)):
    email = request.email.lower()
    account = _get_account_by_email(db, email)
    if not account or not verify_password(request.password, account.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email 或密碼錯誤")

    if account.user_id is None:
        profile = User(name=account.name)
        db.add(profile)
        db.flush()
        account.user_id = profile.id
        db.commit()
        db.refresh(account)

    token = create_access_token(
        {
            "account_id": account.id,
            "email": account.email,
            "name": account.name,
            "user_id": account.user_id,
        }
    )
    return TokenResponse(
        access_token=token,
        token=token,
        user=UserMe(
            account_id=account.id,
            id=account.user_id,
            email=account.email,
            name=account.name,
            user_id=account.user_id,
        ),
    )


@router.get("/me", response_model=UserMe)
async def me(account: AuthAccount = Depends(deps.get_current_account)):
    return UserMe(
        account_id=account.id,
        id=account.user_id,
        email=account.email,
        name=account.name,
        user_id=account.user_id,
    )
