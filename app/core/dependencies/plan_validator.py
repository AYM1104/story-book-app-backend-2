from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.supabase_session import get_supabase_db
from app.models.story.story_setting import StorySetting
from app.service.credits import CreditsService, PricingService
from pydantic import BaseModel, ConfigDict


class PlanValidationResult(BaseModel):
    """プラン検証結果"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    user_id: str
    plan: str
    story_setting: StorySetting


async def validate_story_plan(
    story_setting_id: int,
    story_pages: int,
    db: Session = Depends(get_supabase_db)
) -> PlanValidationResult:
    """
    ストーリー作成のプラン制限を検証する依存関数
    
    Args:
        story_setting_id: ストーリー設定ID
        story_pages: リクエストされたページ数
        db: データベースセッション
        
    Returns:
        PlanValidationResult: 検証済みのユーザー情報とプラン
        
    Raises:
        HTTPException: プラン制限を超えている場合
    """
    print(f"🔍 プラン検証開始: story_setting_id={story_setting_id}, story_pages={story_pages}")
    
    # ストーリー設定を取得
    print(f"📖 StorySetting（ストーリー設定）を取得")
    story_setting = db.query(StorySetting).filter(
        StorySetting.id == story_setting_id
    ).first()
    
    if not story_setting:
        print(f"⚠️ StorySettingが見つかりません: id={story_setting_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ストーリー設定ID {story_setting_id} が見つかりません"
        )
    
    print(f"✅ StorySetting取得成功: id={story_setting.id}")
    
    user_id = story_setting.upload_image.user_id
    print(f"👤 ユーザーID取得: user_id={user_id}")
    
    # ユーザーのプランを取得
    print() # 改行を追加
    print(f"💳 ユーザーのプランを取得: user_id={user_id}")
    user_plan = CreditsService.get_plan(db, user_id)
    print(f"✅ プラン取得完了: plan={user_plan.value}")
    
    # プラン制限チェック
    print(f"🔒 プラン制限チェック: plan={user_plan.value}, requested_pages={story_pages}")
    allowed_pages = PricingService.ALLOWED_PAGES.get(user_plan, [])
    print(f"📋 許可されているページ数: {allowed_pages}")
    
    if not PricingService.is_allowed_for_plan(story_pages, user_plan):
        print(
            f"❌ プラン制限エラー: plan={user_plan.value}, "
            f"requested_pages={story_pages}, allowed_pages={allowed_pages}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "PLAN_LIMIT",
                "message": "現在のプランでは選択されたページ数の絵本を作成できません",
                "plan": user_plan.value,
                "requested_pages": story_pages,
                "allowed_pages": PricingService.ALLOWED_PAGES.get(user_plan, [])
            }
        )
    
    print(f"✅ プラン検証成功: user_id={user_id}, plan={user_plan.value}, story_pages={story_pages}")
    
    return PlanValidationResult(
        user_id=user_id,
        plan=user_plan.value,
        story_setting=story_setting
    )
