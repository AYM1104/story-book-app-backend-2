"""Auth0認証APIエンドポイント"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security.auth0_jwt import get_current_user_auth0, get_auth0_sub_from_token, get_user_or_create
from app.database.supabase_session import get_supabase_db
from app.service.user_account_cleanup_service import user_account_cleanup_service


router = APIRouter(prefix="/auth0", tags=["auth0"])


class UserInfoResponse(BaseModel):
    """ユーザー情報レスポンス"""
    user_id: str
    email: str | None = None
    name: str | None = None
    picture: str | None = None


class StorageCleanupResponse(BaseModel):
    """ストレージ削除結果レスポンス"""
    enabled: bool
    uploads_removed: bool | None = None
    generated_removed: bool | None = None
    error: str | None = None


class Auth0CleanupResponse(BaseModel):
    """Auth0アカウント削除結果レスポンス"""
    enabled: bool
    account_removed: bool | None = None
    error: str | None = None


class AccountDeletionResponse(BaseModel):
    """アカウント削除結果レスポンス"""
    message: str
    user_id: str
    deleted_storybooks: int
    deleted_story_plots: int
    deleted_story_settings: int
    deleted_upload_images: int
    storage_cleanup: StorageCleanupResponse
    auth0_cleanup: Auth0CleanupResponse


@router.get("/me", response_model=UserInfoResponse)
def get_me_auth0(
    payload: dict = Depends(get_current_user_auth0),
    db: Session = Depends(get_supabase_db)
):
    """Auth0トークンを検証し、ユーザー情報を返す
    
    このエンドポイントは、SwiftUIアプリからAuth0でログイン後に
    ユーザー情報を取得するために使用します。
    
    初回ログインの場合は自動的にユーザーを作成し、300クレジットを付与します。
    
    Args:
        payload: Auth0トークンのペイロード（自動的に検証される）
        db: データベースセッション
        
    Returns:
        ユーザー情報
    """
    # ユーザーを取得または作成（初回ログイン時は自動作成＋300クレジット付与）
    user = get_user_or_create(payload, db)
    
    # JWTのsubクレームをuser_idとして返す（sub = Auth0ユーザーID = DBのusers.id）
    return UserInfoResponse(
        user_id=payload.get("sub", ""),  # Auth0のsubクレーム
        email=payload.get("email"),
        name=payload.get("name"),
        picture=payload.get("picture"),
    )


@router.get("/verify")
def verify_token(user_id: str = Depends(get_auth0_sub_from_token)):
    """トークンの有効性を確認する
    
    シンプルなトークン検証エンドポイント。
    Auth0のsubクレーム（ユーザー識別子）を返します。
    
    Args:
        user_id: Auth0のsubクレーム（JWTから自動的に検証・取得される）
        
    Returns:
        検証結果とユーザーID
    """
    return {
        "valid": True,
        "user_id": user_id,  # Auth0のsubクレーム
    }


@router.delete("/me", response_model=AccountDeletionResponse)
def delete_my_account(
    payload: dict = Depends(get_current_user_auth0),
    db: Session = Depends(get_supabase_db),
):
    """現在のユーザーアカウントと関連データを削除"""

    # JWTのsubクレームを取得（Auth0ユーザーID = DBのusers.id）
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ユーザーID（sub）を取得できませんでした",
        )

    try:
        result = user_account_cleanup_service.delete_user_account(user_id=user_id, db=db)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"アカウント削除に失敗しました: {exc}",
        )

    return AccountDeletionResponse(
        message="アカウントを削除しました",
        user_id=result["user_id"],
        deleted_storybooks=result["deleted_storybooks"],
        deleted_story_plots=result["deleted_story_plots"],
        deleted_story_settings=result["deleted_story_settings"],
        deleted_upload_images=result["deleted_upload_images"],
        storage_cleanup=StorageCleanupResponse(**result["storage_cleanup"]),
        auth0_cleanup=Auth0CleanupResponse(**result["auth0_cleanup"]),
    )


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
