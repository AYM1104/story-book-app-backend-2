"""
デバイストークン管理API

プッシュ通知用のデバイストークンを登録・削除するエンドポイント。
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.database.supabase_session import get_supabase_db
from app.core.security.auth0_jwt import get_auth0_sub_from_token
from app.models.device_token import DeviceToken


router = APIRouter(prefix="/api/device-tokens", tags=["device-tokens"])


class RegisterDeviceTokenRequest(BaseModel):
    """デバイストークン登録リクエスト"""
    device_token: str
    platform: str = "ios"  # ios or android


class DeviceTokenResponse(BaseModel):
    """デバイストークンレスポンス"""
    success: bool
    message: str
    device_token_id: Optional[int] = None


@router.post("", response_model=DeviceTokenResponse)
async def register_device_token(
    request: RegisterDeviceTokenRequest,
    db: Session = Depends(get_supabase_db),
    user_id: str = Depends(get_auth0_sub_from_token)
):
    """
    デバイストークンを登録または更新
    
    既に同じトークンが存在する場合はuser_idを更新し、
    同じユーザーの古いトークンは削除される。
    """
    try:
        # 既存のトークンを確認
        existing_token = db.query(DeviceToken).filter(
            DeviceToken.device_token == request.device_token
        ).first()
        
        if existing_token:
            # 既存のトークンがある場合、user_idを更新
            existing_token.user_id = user_id
            existing_token.platform = request.platform
            db.commit()
            return DeviceTokenResponse(
                success=True,
                message="デバイストークンを更新しました",
                device_token_id=existing_token.id
            )
        
        # 新しいトークンを作成
        new_token = DeviceToken(
            user_id=user_id,
            device_token=request.device_token,
            platform=request.platform
        )
        db.add(new_token)
        db.commit()
        db.refresh(new_token)
        
        return DeviceTokenResponse(
            success=True,
            message="デバイストークンを登録しました",
            device_token_id=new_token.id
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"デバイストークンの登録に失敗しました: {str(e)}"
        )


@router.delete("/{token}")
async def delete_device_token(
    token: str,
    db: Session = Depends(get_supabase_db),
    user_id: str = Depends(get_auth0_sub_from_token)
):
    """
    デバイストークンを削除（ログアウト時に呼び出す）
    """
    try:
        # トークンを検索して削除
        device_token = db.query(DeviceToken).filter(
            DeviceToken.device_token == token,
            DeviceToken.user_id == user_id
        ).first()
        
        if not device_token:
            return {"success": True, "message": "トークンは既に削除されています"}
        
        db.delete(device_token)
        db.commit()
        
        return {"success": True, "message": "デバイストークンを削除しました"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"デバイストークンの削除に失敗しました: {str(e)}"
        )
