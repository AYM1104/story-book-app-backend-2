from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.security.jwt_auth import create_access_token, get_current_user


router = APIRouter(prefix="/auth", tags=["auth"])


class GuestLoginRequest(BaseModel):
    device_uuid: str


@router.post("/guest")
def guest_login(req: GuestLoginRequest):
    """デバイスUUIDを受け取り、短期JWTを発行する"""
    # ゲストユーザーは user_id を 0 として扱う
    token = create_access_token(subject="0", expires_minutes=30)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
def get_me(user_id: str = Depends(get_current_user)):
    """JWTを検証し、ユーザーID（=sub）を返す"""
    # ゲスト（user_id == "0"）の場合はユーザー名を "guest" として返す
    if user_id == "0":
        return {"user_id": user_id, "user_name": "guest"}
    # 非ゲストは従来どおり（必要なら別途ユーザー名を引く）
    return {"user_id": user_id, "user_name": None}


