"""
Live Activityトークン管理API

ActivityKit Push Notifications用のプッシュトークンを登録・削除するエンドポイント。
Live Activity開始時にiOSアプリから送信されるActivityKit固有のトークンを管理する。
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.database.supabase_session import get_supabase_db
from app.core.security.auth0_jwt import get_auth0_sub_from_token
from app.models.live_activity_token import LiveActivityToken


router = APIRouter(prefix="/api/live-activity-tokens", tags=["live-activity-tokens"])


class RegisterLiveActivityTokenRequest(BaseModel):
    """Live Activityトークン登録リクエスト"""
    push_token: str
    storybook_id: int


class LiveActivityTokenResponse(BaseModel):
    """Live Activityトークンレスポンス"""
    success: bool
    message: str


@router.post("", response_model=LiveActivityTokenResponse)
async def register_live_activity_token(
    request: RegisterLiveActivityTokenRequest,
    db: Session = Depends(get_supabase_db),
    user_id: str = Depends(get_auth0_sub_from_token)
):
    """
    Live Activityプッシュトークンを登録
    
    iOSアプリでLive Activityが開始された時に呼び出される。
    同じstorybook_idの既存トークンがあれば更新する。
    """
    try:
        # 同じstorybook_idの既存トークンを確認
        existing = db.query(LiveActivityToken).filter(
            LiveActivityToken.storybook_id == request.storybook_id,
            LiveActivityToken.user_id == user_id
        ).first()

        if existing:
            existing.push_token = request.push_token
            db.commit()
            print(f"✅ Live Activityトークン更新: storybook_id={request.storybook_id}")
            return LiveActivityTokenResponse(
                success=True,
                message="Live Activityトークンを更新しました"
            )

        # 新規登録
        new_token = LiveActivityToken(
            user_id=user_id,
            push_token=request.push_token,
            storybook_id=request.storybook_id
        )
        db.add(new_token)
        db.commit()
        print(f"✅ Live Activityトークン登録: storybook_id={request.storybook_id}")

        return LiveActivityTokenResponse(
            success=True,
            message="Live Activityトークンを登録しました"
        )

    except Exception as e:
        db.rollback()
        print(f"❌ Live Activityトークン登録エラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Live Activityトークンの登録に失敗しました: {str(e)}"
        )


@router.delete("/{storybook_id}")
async def delete_live_activity_token(
    storybook_id: int,
    db: Session = Depends(get_supabase_db),
    user_id: str = Depends(get_auth0_sub_from_token)
):
    """
    Live Activityトークンを削除（完了後のクリーンアップ）
    """
    try:
        tokens = db.query(LiveActivityToken).filter(
            LiveActivityToken.storybook_id == storybook_id,
            LiveActivityToken.user_id == user_id
        ).all()

        for token in tokens:
            db.delete(token)
        db.commit()

        return {"success": True, "message": f"Live Activityトークンを削除しました（{len(tokens)}件）"}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Live Activityトークンの削除に失敗しました: {str(e)}"
        )
