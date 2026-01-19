from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserMe(BaseModel):
    account_id: str
    # Backward-compatible field: existing clients used `user.id` as the profile user_id.
    id: Optional[str] = None
    email: EmailStr
    name: Optional[str] = None
    user_id: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    # Backward-compatible field: existing clients used `token`.
    token: Optional[str] = None
    token_type: str = "bearer"
    user: UserMe
