from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database.supabase_session import get_supabase_db
from app.core.security.auth0_jwt import get_auth0_sub_from_token, get_current_user_auth0, get_user_or_create
from app.service.credits import PricingService, CreditsService
from app.models.credits.subscription import PlanType

router = APIRouter(prefix="/pricing", tags=["pricing"])

@router.get("/generate-quote")
def generate_quote(
    story_pages: int = Query(..., description="物語ページ数（3, 5, 7, 10のいずれか）", ge=3, le=10),
    payload: dict = Depends(get_current_user_auth0),  # JWTペイロード
    db: Session = Depends(get_supabase_db)
):
    """クレジット見積もりを生成
    
    初回ログインの場合は自動的にユーザーを作成し、300クレジットを付与します。
    
    Args:
        story_pages: 物語ページ数
        payload: JWTペイロード（自動的に検証される）
        db: データベースセッション
        
    Returns:
        {
            "required_credits": 必要クレジット数,
            "total_pages": 合計ページ数（表紙込み）
        }
        
    Raises:
        HTTPException: 無効なページ数の場合、またはプランで許可されていない場合
    """
    # ユーザーを取得または作成（初回ログイン時は自動作成＋300クレジット付与）
    user = get_user_or_create(payload, db)
    
    # プランを取得
    plan = CreditsService.get_plan(db, user.id)
    
    # プランで許可されているページ数か確認
    if not PricingService.is_allowed_for_plan(story_pages, plan):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "PLAN_LIMIT",
                "message": "Your plan does not allow the requested story pages",
                "plan": plan.value,
                "requested_pages": story_pages,
                "allowed_pages": PricingService.ALLOWED_PAGES.get(plan, [])
            }
        )
    
    # 見積もりを生成
    try:
        quote = PricingService.generate_quote(story_pages)
        return quote
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_PAGES",
                "message": str(e)
            }
        )

