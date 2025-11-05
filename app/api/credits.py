from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.supabase_session import get_supabase_db
from app.core.security.auth0_jwt import get_auth0_sub_from_token, get_current_user_auth0, get_user_or_create
from app.service.credits import CreditsService
from app.models.credits.subscription import PlanType

router = APIRouter(prefix="/credits", tags=["credits"])

@router.get("/me")
def get_my_credits(
    payload: dict = Depends(get_current_user_auth0),  # JWTペイロード
    db: Session = Depends(get_supabase_db)
):
    """現在のユーザーのクレジット残高とプランを取得
    
    初回ログインの場合は自動的にユーザーを作成し、300クレジットを付与します。
    
    Args:
        payload: JWTペイロード（自動的に検証される）
        db: データベースセッション
        
    Returns:
        {
            "balance": クレジット残高,
            "plan": プランタイプ（FREE, STARTER, PLUS, PREMIUM）
        }
    """
    # ユーザーを取得または作成（初回ログイン時は自動作成＋300クレジット付与）
    user = get_user_or_create(payload, db)
    
    balance = CreditsService.get_balance(db, user.id)
    plan = CreditsService.get_plan(db, user.id)
    
    return {
        "balance": balance,
        "plan": plan.value
    }

