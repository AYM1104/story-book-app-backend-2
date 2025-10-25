import os
import time
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt

from app.core.security.auth0_jwt import verify_auth0_token


# 環境変数からシークレットと設定を取得
JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET") or os.getenv("JWT_SECRET", "change_me_dev_secret")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRES_MINUTES_DEFAULT: int = int(os.getenv("JWT_EXPIRES_MINUTES", "30"))


def create_access_token(*, subject: str, expires_minutes: Optional[int] = None) -> str:
    """短期JWTを発行する

    Args:
        subject: トークンの主体（ここでは user_id 互換として device_uuid を想定）
        expires_minutes: 有効期限（分）。未指定時は既定値
    """
    if not JWT_SECRET:
        raise RuntimeError("JWTシークレットが設定されていません。SUPABASE_JWT_SECRET もしくは JWT_SECRET を設定してください。")

    now = int(time.time())
    minutes = expires_minutes if expires_minutes is not None else JWT_EXPIRES_MINUTES_DEFAULT
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + minutes * 60,
        "typ": "access",
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    # PyJWT v2 は str を返す
    return token


http_bearer = HTTPBearer(auto_error=True)


def _decode_internal_token(token: str) -> Optional[str]:
    """内部JWTシークレットを使用したトークン検証。失敗した場合はNoneを返す。"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        subject = payload.get("sub")
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: subject not found",
            )
        return subject
    except jwt.ExpiredSignatureError:
        # 内部トークンの期限切れは即座にエラーを返す
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        # 内部JWTではない可能性があるため後段にフォールバック
        return None


def _decode_auth0_token(token: str) -> str:
    """Auth0由来のトークンを検証してユーザーID(sub)を返す。"""
    payload = verify_auth0_token(token)
    subject = payload.get("sub")
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: subject not found",
        )
    return subject


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(http_bearer)) -> str:
    """Authorization: Bearer トークンを検証し、user_id（=sub）を返す

    1. 既存のアプリ専用JWTを検証
    2. 検証できなかった場合はAuth0トークンとして検証

    Returns:
        user_id として利用する subject
    """
    token = credentials.credentials

    # まずは従来のJWTシークレットで検証
    subject = _decode_internal_token(token)
    if subject is not None:
        return subject

    # 内部トークンとして無効だった場合はAuth0トークンとして検証
    return _decode_auth0_token(token)

