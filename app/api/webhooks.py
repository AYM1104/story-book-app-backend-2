"""
App Store Server Notifications Webhook
App Storeからのサーバー通知を受信して処理する
"""

from fastapi import APIRouter, Request, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from app.database.supabase_session import get_supabase_db
from app.models.credits.subscription import Subscription, PlanType
from app.models.iap.app_store_transaction import AppStoreTransaction
from app.service.appstore import JWSVerificationService
from app.service.credits.credits_service import CreditsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


# ===== 通知タイプ定義 =====

class NotificationType:
    """App Store Server Notifications V2の通知タイプ"""
    SUBSCRIBED = "SUBSCRIBED"                          # 新規サブスクリプション
    DID_RENEW = "DID_RENEW"                            # サブスクリプション更新
    DID_CHANGE_RENEWAL_STATUS = "DID_CHANGE_RENEWAL_STATUS"  # 自動更新設定変更
    DID_FAIL_TO_RENEW = "DID_FAIL_TO_RENEW"            # 更新失敗
    GRACE_PERIOD_EXPIRED = "GRACE_PERIOD_EXPIRED"      # グレースピリオド終了
    EXPIRED = "EXPIRED"                                # 期限切れ
    REFUND = "REFUND"                                  # 返金
    REVOKE = "REVOKE"                                  # 取り消し


# ===== ヘルパー関数 =====

def product_id_to_plan_type(product_id: str) -> PlanType:
    """プロダクトIDからPlanTypeを取得"""
    mapping = {
        "com.ehonnotane.subscription.starter": PlanType.STARTER,
        "com.ehonnotane.subscription.plus": PlanType.PLUS,
        "com.ehonnotane.subscription.premium": PlanType.PREMIUM,
    }
    return mapping.get(product_id, PlanType.FREE)


def plan_type_to_credits(plan_type: PlanType) -> int:
    """PlanTypeから付与するクレジット数を取得"""
    mapping = {
        PlanType.STARTER: 350,
        PlanType.PLUS: 700,
        PlanType.PREMIUM: 1200,
    }
    return mapping.get(plan_type, 0)


def parse_iso_datetime(iso_string: str) -> Optional[datetime]:
    """ISO 8601形式の日時文字列をdatetimeに変換"""
    if not iso_string:
        return None
    try:
        return datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
    except Exception:
        return None


# ===== Webhookエンドポイント =====

@router.post("/appstore")
async def app_store_server_notifications(request: Request):
    """
    App Store Server Notifications V2のWebhookエンドポイント
    
    App Storeからのサブスクリプション状態変更通知を受信し、
    データベースを更新します。
    
    重要: App Storeは200 OKレスポンスを期待するため、
    処理結果に関わらず必ず200を返します。
    """
    try:
        # リクエストボディを取得
        body = await request.json()
        signed_payload = body.get("signedPayload")
        
        if not signed_payload:
            logger.warning("⚠️ signedPayloadが含まれていません")
            return {"status": "received"}
        
        # JWS検証
        try:
            payload = JWSVerificationService.verify_jws(signed_payload)
            logger.info(f"✅ Server Notification JWS検証成功")
        except ValueError as e:
            logger.error(f"❌ Server Notification JWS検証失敗: {str(e)}")
            # JWS検証失敗でも200を返す（App Storeの要件）
            return {"status": "received"}
        
        # 通知タイプを取得
        notification_type = payload.get("notificationType")
        subtype = payload.get("subtype")
        
        logger.info(f"📬 Server Notification受信: type={notification_type}, subtype={subtype}")
        
        # データセクションを取得
        data = payload.get("data", {})
        signed_transaction_info = data.get("signedTransactionInfo")
        signed_renewal_info = data.get("signedRenewalInfo")
        
        if not signed_transaction_info:
            logger.warning("⚠️ signed_transaction_info が含まれていません")
            return {"status": "received"}
        
        # トランザクション情報をデコード
        try:
            transaction_payload = JWSVerificationService.verify_jws(signed_transaction_info)
        except ValueError as e:
            logger.error(f"❌ トランザクション情報のJWS検証失敗: {str(e)}")
            return {"status": "received"}
        
        # 更新情報をデコード（オプション）
        renewal_payload = None
        if signed_renewal_info:
            try:
                renewal_payload = JWSVerificationService.verify_jws(signed_renewal_info)
            except ValueError as e:
                logger.warning(f"⚠️ 更新情報のJWS検証失敗: {str(e)}")
        
        # データベースセッションを取得
        db = next(get_supabase_db())
        
        try:
            # 通知タイプ別に処理
            await process_notification(
                db=db,
                notification_type=notification_type,
                subtype=subtype,
                transaction_payload=transaction_payload,
                renewal_payload=renewal_payload
            )
            
            db.commit()
            logger.info(f"✅ Server Notification処理完了: {notification_type}")
            
        except Exception as e:
            logger.error(f"❌ Server Notification処理エラー: {str(e)}", exc_info=True)
            db.rollback()
        finally:
            db.close()
        
        # 常に200 OKを返す
        return {"status": "received"}
        
    except Exception as e:
        logger.error(f"❌ Webhook処理エラー: {str(e)}", exc_info=True)
        # エラーが発生しても200を返す
        return {"status": "received"}


async def process_notification(
    db: Session,
    notification_type: str,
    subtype: Optional[str],
    transaction_payload: Dict[str, Any],
    renewal_payload: Optional[Dict[str, Any]]
):
    """
    通知タイプに応じて処理を実行
    
    Args:
        db: データベースセッション
        notification_type: 通知タイプ
        subtype: サブタイプ
        transaction_payload: デコードされたトランザクション情報
        renewal_payload: デコードされた更新情報（オプション）
    """
    # トランザクション情報を抽出
    transaction_id = transaction_payload.get("transactionId")
    original_transaction_id = transaction_payload.get("originalTransactionId")
    product_id = transaction_payload.get("productId")
    purchase_date_ms = transaction_payload.get("purchaseDate")
    expires_date_ms = transaction_payload.get("expiresDate")
    
    # ミリ秒からdatetimeに変換
    purchase_date = datetime.fromtimestamp(purchase_date_ms / 1000) if purchase_date_ms else None
    expires_date = datetime.fromtimestamp(expires_date_ms / 1000) if expires_date_ms else None
    
    # ユーザーIDを取得（original_transaction_idから既存サブスクリプションを検索）
    subscription = db.query(Subscription).filter(
        Subscription.original_transaction_id == original_transaction_id
    ).first()
    
    if not subscription:
        # サブスクリプションが見つからない場合、app_store_transactionsから検索
        app_store_transaction = db.query(AppStoreTransaction).filter(
            AppStoreTransaction.original_transaction_id == original_transaction_id
        ).first()
        
        if app_store_transaction:
            user_id = app_store_transaction.user_id
        else:
            logger.warning(f"⚠️ ユーザーが見つかりません: original_transaction_id={original_transaction_id}")
            return
    else:
        user_id = subscription.user_id
    
    # トランザクションを保存
    existing_transaction = db.query(AppStoreTransaction).filter(
        AppStoreTransaction.transaction_id == transaction_id
    ).first()
    
    if not existing_transaction:
        app_store_transaction = AppStoreTransaction(
            user_id=user_id,
            transaction_id=transaction_id,
            original_transaction_id=original_transaction_id,
            product_id=product_id,
            purchase_date=purchase_date,
            expires_date=expires_date,
            notification_type=notification_type
        )
        db.add(app_store_transaction)
        logger.info(f"📝 トランザクション保存: {transaction_id}")
    
    # 通知タイプ別処理
    if notification_type == NotificationType.SUBSCRIBED:
        await handle_subscribed(db, user_id, product_id, original_transaction_id, transaction_id, expires_date)
    
    elif notification_type == NotificationType.DID_RENEW:
        await handle_did_renew(db, user_id, product_id, transaction_id, expires_date, subscription)
    
    elif notification_type == NotificationType.DID_CHANGE_RENEWAL_STATUS:
        await handle_renewal_status_change(db, subscription, renewal_payload)
    
    elif notification_type == NotificationType.DID_FAIL_TO_RENEW:
        await handle_did_fail_to_renew(db, subscription)
    
    elif notification_type == NotificationType.GRACE_PERIOD_EXPIRED:
        await handle_grace_period_expired(db, subscription)
    
    elif notification_type == NotificationType.EXPIRED:
        await handle_expired(db, subscription)
    
    elif notification_type == NotificationType.REFUND:
        await handle_refund(db, user_id, transaction_id, product_id)
    
    elif notification_type == NotificationType.REVOKE:
        await handle_revoke(db, subscription)


# ===== 通知タイプ別ハンドラー =====

async def handle_subscribed(
    db: Session,
    user_id: str,
    product_id: str,
    original_transaction_id: str,
    transaction_id: str,
    expires_date: Optional[datetime]
):
    """新規サブスクリプション登録"""
    plan_type = product_id_to_plan_type(product_id)
    credits_to_grant = plan_type_to_credits(plan_type)
    
    subscription = Subscription(
        user_id=user_id,
        plan_type=plan_type,
        original_transaction_id=original_transaction_id,
        latest_transaction_id=transaction_id,
        product_id=product_id,
        auto_renew_status=True,
        expires_at=expires_date,
        last_credit_grant_date=datetime.utcnow()
    )
    db.add(subscription)
    
    # クレジット付与
    CreditsService.add_credits(
        db=db,
        user_id=user_id,
        delta=credits_to_grant,
        reason="subscription_started",
        transaction_id=transaction_id
    )
    
    logger.info(f"🆕 新規サブスクリプション: user={user_id}, plan={plan_type}, credits={credits_to_grant}")


async def handle_did_renew(
    db: Session,
    user_id: str,
    product_id: str,
    transaction_id: str,
    expires_date: Optional[datetime],
    subscription: Optional[Subscription]
):
    """サブスクリプション更新"""
    if not subscription:
        logger.warning(f"⚠️ サブスクリプションが見つかりません: user_id={user_id}")
        return
    
    plan_type = product_id_to_plan_type(product_id)
    credits_to_grant = plan_type_to_credits(plan_type)
    
    # サブスクリプション更新
    subscription.latest_transaction_id = transaction_id
    subscription.expires_at = expires_date
    subscription.last_credit_grant_date = datetime.utcnow()
    
    # クレジット付与
    CreditsService.add_credits(
        db=db,
        user_id=user_id,
        delta=credits_to_grant,
        reason="subscription_renewed",
        transaction_id=transaction_id
    )
    
    logger.info(f"♻️ サブスクリプション更新: user={user_id}, credits={credits_to_grant}")


async def handle_renewal_status_change(
    db: Session,
    subscription: Optional[Subscription],
    renewal_payload: Optional[Dict[str, Any]]
):
    """自動更新設定変更"""
    if not subscription or not renewal_payload:
        return
    
    will_auto_renew = renewal_payload.get("autoRenewStatus") == 1
    subscription.auto_renew_status = will_auto_renew
    
    logger.info(f"🔄 自動更新設定変更: user={subscription.user_id}, auto_renew={will_auto_renew}")


async def handle_did_fail_to_renew(db: Session, subscription: Optional[Subscription]):
    """更新失敗（請求リトライ開始）"""
    if not subscription:
        return
    
    subscription.is_in_billing_retry = True
    logger.warning(f"⚠️ 更新失敗（請求リトライ中）: user={subscription.user_id}")


async def handle_grace_period_expired(db: Session, subscription: Optional[Subscription]):
    """グレースピリオド終了"""
    if not subscription:
        return
    
    subscription.is_in_billing_retry = False
    subscription.grace_period_expires_at = None
    logger.warning(f"❌ グレースピリオド終了: user={subscription.user_id}")


async def handle_expired(db: Session, subscription: Optional[Subscription]):
    """サブスクリプション期限切れ"""
    if not subscription:
        return
    
    subscription.auto_renew_status = False
    logger.info(f"⏰ サブスクリプション期限切れ: user={subscription.user_id}")


async def handle_refund(db: Session, user_id: str, transaction_id: str, product_id: str):
    """返金処理（クレジット取り消し）"""
    plan_type = product_id_to_plan_type(product_id)
    credits_to_deduct = plan_type_to_credits(plan_type)
    
    # クレジットを減算
    CreditsService.spend_credits(
        db=db,
        user_id=user_id,
        delta=credits_to_deduct,
        reason=f"refund_{transaction_id}"
    )
    
    logger.warning(f"💸 返金処理: user={user_id}, credits_deducted={credits_to_deduct}")


async def handle_revoke(db: Session, subscription: Optional[Subscription]):
    """取り消し"""
    if not subscription:
        return
    
    subscription.auto_renew_status = False
    subscription.cancellation_date = datetime.utcnow()
    logger.warning(f"🚫 サブスクリプション取り消し: user={subscription.user_id}")
