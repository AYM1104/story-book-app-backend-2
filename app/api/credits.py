from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.database.supabase_session import get_supabase_db
from app.core.security.auth0_jwt import get_auth0_sub_from_token, get_current_user_auth0, get_user_or_create
from app.service.credits import CreditsService
from app.models.credits.subscription import PlanType

router = APIRouter(prefix="/credits", tags=["credits"])


# クレジット購入リクエストスキーマ
class PurchaseCreditsRequest(BaseModel):
    amount: int = Field(..., gt=0, description="購入するクレジット数（正の値）")


# クレジット購入レスポンススキーマ
class PurchaseCreditsResponse(BaseModel):
    success: bool
    message: str
    balance: int  # 更新後の残高
    purchased_amount: int  # 購入したクレジット数

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
    try:
        # ユーザーを取得または作成（初回ログイン時は自動作成＋300クレジット付与）
        user = get_user_or_create(payload, db)
        
        balance = CreditsService.get_balance(db, user.id)
        plan = CreditsService.get_plan(db, user.id)
        
        return {
            "balance": balance,
            "plan": plan.value
        }
    except HTTPException:
        # HTTPExceptionはそのまま再スロー
        raise
    except Exception as e:
        # その他のエラーは500エラーとして返す（詳細なエラーメッセージを含む）
        import traceback
        error_detail = f"クレジット情報の取得中にエラーが発生しました: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )


@router.post("/purchase", response_model=PurchaseCreditsResponse)
def purchase_credits(
    request: PurchaseCreditsRequest,
    payload: dict = Depends(get_current_user_auth0),  # JWTペイロード
    db: Session = Depends(get_supabase_db)
):
    """クレジットを購入してbalanceを更新するエンドポイント
    
    購入したクレジット数がusersテーブルのbalanceカラムに反映されます。
    
    Args:
        request: 購入リクエスト（購入するクレジット数）
        payload: JWTペイロード（自動的に検証される）
        db: データベースセッション
        
    Returns:
        {
            "success": 成功フラグ,
            "message": メッセージ,
            "balance": 更新後の残高,
            "purchased_amount": 購入したクレジット数
        }
    """
    # ユーザーを取得または作成（初回ログイン時は自動作成＋300クレジット付与）
    user = get_user_or_create(payload, db)
    
    # クレジットを付与（balanceが自動的に更新される）
    CreditsService.add_credits(
        db=db,
        user_id=user.id,
        amount=request.amount,
        reason="purchase"
    )
    
    # 更新後の残高を取得
    updated_balance = CreditsService.get_balance(db, user.id)
    
    return PurchaseCreditsResponse(
        success=True,
        message=f"{request.amount}クレジットを購入しました",
        balance=updated_balance,
        purchased_amount=request.amount
    )

