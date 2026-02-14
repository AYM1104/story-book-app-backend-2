"""
サブスクリプション関連のAPIエンドポイント
"""
import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import logging

from app.database.supabase_session import get_supabase_db
from app.core.security.auth0_jwt import get_current_user_auth0, get_user_or_create
from app.models.credits.subscription import Subscription, PlanType
from app.models.iap.app_store_transaction import AppStoreTransaction
from app.service.appstore import JWSVerificationService
from app.service.credits.credits_service import CreditsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])


# ===== リクエスト/レスポンスモデル =====

class TransactionData(BaseModel):
    """トランザクションデータ"""
    id: str = Field(..., description="トランザクションID")
    originalTransactionId: str = Field(..., description="オリジナルトランザクションID")
    productId: str = Field(..., description="プロダクトID")
    purchaseDate: str = Field(..., description="購入日時（ISO 8601形式）")
    expiresDate: Optional[str] = Field(None, description="有効期限（ISO 8601形式）")
    jwsRepresentation: str = Field(..., description="JWS形式のトランザクション")


class VerifyTransactionRequest(BaseModel):
    """トランザクション検証リクエスト"""
    transaction: TransactionData


class SubscriptionResponse(BaseModel):
    """サブスクリプション情報レスポンス"""
    id: int
    userId: str
    planType: str
    productId: str
    status: str
    expiresAt: Optional[str]
    autoRenewStatus: bool


class VerifyTransactionResponse(BaseModel):
    """トランザクション検証レスポンス"""
    success: bool
    subscription: SubscriptionResponse
    creditsGranted: int
    totalCredits: int


class SubscriptionStatusResponse(BaseModel):
    """サブスクリプション状態レスポンス"""
    subscription: Optional[SubscriptionResponse]
    credits: dict


# ===== ヘルパー関数 =====

def product_id_to_plan_type(product_id: str) -> PlanType:
    """プロダクトIDからPlanTypeを取得"""
    mapping = {
        "com.ehonnotane.subscription.starter": PlanType.STARTER,
        "com.ehonnotane.subscription.plus": PlanType.PLUS,
        "com.ehonnotane.subscription.premium": PlanType.PREMIUM,
    }
    
    plan_type = mapping.get(product_id)
    if not plan_type:
        raise ValueError(f"不明なプロダクトID: {product_id}")
    
    return plan_type


def plan_type_to_credits(plan_type: PlanType) -> int:
    """PlanTypeから付与するクレジット数を取得"""
    mapping = {
        PlanType.STARTER: 600,
        PlanType.PLUS: 1000,
        PlanType.PREMIUM: 1500,
    }
    return mapping.get(plan_type, 0)


# ===== APIエンドポイント =====

@router.post("/verify", response_model=VerifyTransactionResponse)
async def verify_transaction(
    request: VerifyTransactionRequest,
    payload: dict = Depends(get_current_user_auth0),
    db: Session = Depends(get_supabase_db)
):
    """
    トランザクションを検証し、サブスクリプションとクレジットを登録
    
    1. JWS検証
    2. トランザクション重複チェック
    3. サブスクリプション登録/更新
    4. クレジット付与
    """
    try:
        # ユーザーを取得または作成
        current_user = get_user_or_create(payload, db)
        
        transaction_data = request.transaction
        
        # JWS検証（またはXcode/Sandbox環境のJSON直接パース）
        jws_data = transaction_data.jwsRepresentation
        jws_payload = None
        
        # JWSかJSONかを判定：JWSは "header.payload.signature" 形式（ドットで3分割）
        # Xcode/Sandbox環境ではjsonRepresentationがそのまま送信される（JSON文字列）
        is_raw_json = False
        try:
            parsed = json.loads(jws_data)
            if isinstance(parsed, dict):
                is_raw_json = True
        except (json.JSONDecodeError, TypeError):
            pass
        
        if is_raw_json:
            # JSON直接パース（Xcode/Sandbox環境）
            jws_payload = parsed
            environment = jws_payload.get("environment", "Unknown")
            
            if environment not in ("Xcode", "Sandbox"):
                logger.warning(f"⚠️ 非本番環境のJSONトランザクション: environment={environment}")
            
            logger.info(f"✅ JSONトランザクション検証（{environment}環境）: transaction_id={transaction_data.id}")
        else:
            # JWS検証（本番環境）
            try:
                jws_payload = JWSVerificationService.verify_jws(jws_data)
                logger.info(f"✅ JWS検証成功: transaction_id={transaction_data.id}")
            except ValueError as e:
                logger.error(f"❌ JWS検証失敗: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "INVALID_TRANSACTION",
                        "message": "トランザクションの検証に失敗しました",
                        "details": str(e)
                    }
                )
        
        # トランザクション重複チェック
        existing_transaction = db.query(AppStoreTransaction).filter(
            AppStoreTransaction.transaction_id == transaction_data.id
        ).first()
        
        if existing_transaction:
            logger.warning(f"⚠️ 重複トランザクション: {transaction_data.id}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "DUPLICATE_TRANSACTION",
                    "message": "このトランザクションは既に処理されています"
                }
            )
        
        # トランザクションをデータベースに保存
        app_store_transaction = AppStoreTransaction(
            user_id=current_user.id,
            transaction_id=transaction_data.id,
            original_transaction_id=transaction_data.originalTransactionId,
            product_id=transaction_data.productId,
            purchase_date=datetime.fromisoformat(transaction_data.purchaseDate.replace('Z', '+00:00')),
            expires_date=datetime.fromisoformat(transaction_data.expiresDate.replace('Z', '+00:00')) if transaction_data.expiresDate else None,
            jws_representation=transaction_data.jwsRepresentation,
            notification_type="PURCHASE"  # 手動検証の場合
        )
        db.add(app_store_transaction)
        
        # プランタイプを取得
        plan_type = product_id_to_plan_type(transaction_data.productId)
        credits_to_grant = plan_type_to_credits(plan_type)
        
        # サブスクリプションを取得または作成
        subscription = db.query(Subscription).filter(
            Subscription.user_id == current_user.id
        ).first()
        
        if not subscription:
            # 新規サブスクリプション
            subscription = Subscription(
                user_id=current_user.id,
                plan_type=plan_type,
                original_transaction_id=transaction_data.originalTransactionId,
                latest_transaction_id=transaction_data.id,
                product_id=transaction_data.productId,
                auto_renew_status=True,
                expires_at=datetime.fromisoformat(transaction_data.expiresDate.replace('Z', '+00:00')) if transaction_data.expiresDate else None,
                last_credit_grant_date=datetime.utcnow()
            )
            db.add(subscription)
            logger.info(f"📝 新規サブスクリプション作成: user_id={current_user.id}, plan={plan_type}")
        else:
            # 既存サブスクリプション更新
            subscription.plan_type = plan_type
            subscription.latest_transaction_id = transaction_data.id
            subscription.product_id = transaction_data.productId
            subscription.expires_at = datetime.fromisoformat(transaction_data.expiresDate.replace('Z', '+00:00')) if transaction_data.expiresDate else None
            subscription.last_credit_grant_date = datetime.utcnow()
            logger.info(f"♻️ サブスクリプション更新: user_id={current_user.id}, plan={plan_type}")
        
        # クレジット付与
        CreditsService.add_credits(
            db=db,
            user_id=current_user.id,
            delta=credits_to_grant,
            reason="subscription_started",
            transaction_id=transaction_data.id
        )
        
        # 変更をコミット
        db.commit()
        db.refresh(subscription)
        
        # 現在のクレジット残高を取得
        total_credits = CreditsService.get_balance(db, current_user.id)
        
        logger.info(f"✅ トランザクション検証完了: user={current_user.id}, credits_granted={credits_to_grant}, total={total_credits}")
        
        return VerifyTransactionResponse(
            success=True,
            subscription=SubscriptionResponse(
                id=subscription.id,
                userId=subscription.user_id,
                planType=subscription.plan_type.value,
                productId=subscription.product_id,
                status="active",
                expiresAt=subscription.expires_at.isoformat() if subscription.expires_at else None,
                autoRenewStatus=subscription.auto_renew_status or False
            ),
            creditsGranted=credits_to_grant,
            totalCredits=total_credits
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ トランザクション検証エラー: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "サーバーエラーが発生しました",
                "details": str(e)
            }
        )


@router.get("/status", response_model=SubscriptionStatusResponse)
async def get_subscription_status(
    payload: dict = Depends(get_current_user_auth0),
    db: Session = Depends(get_supabase_db)
):
    """
    ユーザーの現在のサブスクリプション状態を取得
    """
    try:
        # ユーザーを取得または作成
        current_user = get_user_or_create(payload, db)
        
        # サブスクリプション取得
        subscription = db.query(Subscription).filter(
            Subscription.user_id == current_user.id
        ).first()
        
        # クレジット残高取得
        balance = CreditsService.get_balance(db, current_user.id)
        
        if subscription:
            # 有効期限チェック
            is_active = True
            if subscription.expires_at:
                is_active = subscription.expires_at > datetime.utcnow()
            
            subscription_response = SubscriptionResponse(
                id=subscription.id,
                userId=subscription.user_id,
                planType=subscription.plan_type.value,
                productId=subscription.product_id or "",
                status="active" if is_active else "expired",
                expiresAt=subscription.expires_at.isoformat() if subscription.expires_at else None,
                autoRenewStatus=subscription.auto_renew_status or False
            )
            
            monthly_allocation = plan_type_to_credits(subscription.plan_type)
            next_grant_date = subscription.expires_at.isoformat() if subscription.expires_at else None
        else:
            subscription_response = None
            monthly_allocation = 0
            next_grant_date = None
        
        return SubscriptionStatusResponse(
            subscription=subscription_response,
            credits={
                "balance": balance,
                "monthlyAllocation": monthly_allocation,
                "nextGrantDate": next_grant_date
            }
        )
        
    except Exception as e:
        logger.error(f"❌ サブスクリプション状態取得エラー: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "サーバーエラーが発生しました"
            }
        )
