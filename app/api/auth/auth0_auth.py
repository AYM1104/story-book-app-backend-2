"""Auth0認証APIエンドポイント"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.security.auth0_jwt import get_current_user_auth0, get_user_id_auth0


router = APIRouter(prefix="/auth0", tags=["auth0"])


class UserInfoResponse(BaseModel):
    """ユーザー情報レスポンス"""
    user_id: str
    email: str | None = None
    name: str | None = None
    picture: str | None = None


@router.get("/me", response_model=UserInfoResponse)
def get_me_auth0(payload: dict = Depends(get_current_user_auth0)):
    """Auth0トークンを検証し、ユーザー情報を返す
    
    このエンドポイントは、SwiftUIアプリからAuth0でログイン後に
    ユーザー情報を取得するために使用します。
    
    Args:
        payload: Auth0トークンのペイロード（自動的に検証される）
        
    Returns:
        ユーザー情報
    """
    return UserInfoResponse(
        user_id=payload.get("sub", ""),
        email=payload.get("email"),
        name=payload.get("name"),
        picture=payload.get("picture"),
    )


@router.get("/verify")
def verify_token(user_id: str = Depends(get_user_id_auth0)):
    """トークンの有効性を確認する
    
    シンプルなトークン検証エンドポイント。
    ユーザーIDのみを返します。
    
    Args:
        user_id: Auth0ユーザーID（自動的に検証される）
        
    Returns:
        検証結果とユーザーID
    """
    return {
        "valid": True,
        "user_id": user_id,
    }


@router.get("/health")
def health_check():
    """Auth0認証システムのヘルスチェック
    
    認証なしでアクセス可能なエンドポイント。
    Auth0の設定が正しいか確認します。
    """
    from app.core.security.auth0_config import Auth0Config
    
    try:
        Auth0Config.validate()
        return {
            "status": "ok",
            "auth0_domain": Auth0Config.DOMAIN,
            "issuer": Auth0Config.get_issuer(),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Auth0設定エラー: {str(e)}",
        )

