from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from app.models.credits.credit_ledger import CreditLedger
from app.models.credits.subscription import Subscription, PlanType
from app.models.users.users import Users

class CreditsService:
    """クレジット管理サービス"""
    
    @staticmethod
    def get_balance(db: Session, user_id: str) -> int:
        """ユーザーのクレジット残高を取得
        
        Args:
            db: データベースセッション
            user_id: ユーザーID
            
        Returns:
            クレジット残高
        """
        user = db.query(Users).filter(Users.id == user_id).first()
        if user:
            return user.balance if user.balance is not None else 0
        
        # ユーザーが存在しない場合は0を返す
        return 0
    
    @staticmethod
    def get_plan(db: Session, user_id: str) -> PlanType:
        """ユーザーのプランを取得
        
        Args:
            db: データベースセッション
            user_id: ユーザーID
            
        Returns:
            プランタイプ（デフォルトはFREE）
        """
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user_id
        ).first()
        
        return subscription.plan if subscription else PlanType.FREE
    
    @staticmethod
    def add_credits(
        db: Session,
        user_id: str,
        amount: int,
        reason: str,
        work_id: Optional[int] = None
    ) -> CreditLedger:
        """クレジットを付与
        
        Args:
            db: データベースセッション
            user_id: ユーザーID
            amount: 付与するクレジット数（正の値）
            reason: 付与理由
            work_id: 関連する作品ID（オプション）
            
        Returns:
            作成されたCreditLedgerレコード
        """
        # ユーザーを取得して残高を更新
        user = db.query(Users).filter(Users.id == user_id).first()
        if not user:
            raise ValueError(f"ユーザーID {user_id} が見つかりません")
        
        # 台帳に記録
        credit_entry = CreditLedger(
            user_id=user_id,
            delta=amount,
            reason=reason,
            work_id=work_id
        )
        db.add(credit_entry)
        
        # ユーザーの残高を更新
        if user.balance is None:
            user.balance = 0
        user.balance += amount
        
        db.commit()
        db.refresh(credit_entry)
        return credit_entry
    
    @staticmethod
    def spend_credits(
        db: Session,
        user_id: str,
        amount: int,
        reason: str,
        work_id: Optional[int] = None,
        auto_commit: bool = True
    ) -> CreditLedger:
        """クレジットを消費
        
        Args:
            db: データベースセッション
            user_id: ユーザーID
            amount: 消費するクレジット数（正の値として渡す）
            reason: 消費理由
            work_id: 関連する作品ID（オプション）
            auto_commit: 自動コミットするかどうか（デフォルト: True）
            
        Returns:
            作成されたCreditLedgerレコード
            
        Raises:
            ValueError: 残高が不足している場合
        """
        # ユーザーを取得して残高を確認・更新（排他ロックを取得）
        user = db.query(Users).filter(Users.id == user_id).with_for_update().first()
        if not user:
            raise ValueError(f"ユーザーID {user_id} が見つかりません")
        
        # 残高を確認
        current_balance = user.balance if user.balance is not None else 0
        if current_balance < amount:
            raise ValueError(f"残高不足: 残高={current_balance}, 必要={amount}")
        
        # 台帳に記録
        credit_entry = CreditLedger(
            user_id=user_id,
            delta=-amount,
            reason=reason,
            work_id=work_id
        )
        db.add(credit_entry)
        
        # ユーザーの残高を更新
        user.balance -= amount
        
        if auto_commit:
            db.commit()
            db.refresh(credit_entry)
        else:
            # 外側でコミットする場合、flushしてIDを取得可能にする
            db.flush()
        return credit_entry
    
    @staticmethod
    def ensure_subscription(db: Session, user_id: str, plan: PlanType = PlanType.FREE) -> Subscription:
        """サブスクリプションを確保（存在しない場合は作成）
        
        Args:
            db: データベースセッション
            user_id: ユーザーID
            plan: プランタイプ（デフォルトはFREE）
            
        Returns:
            Subscriptionレコード
        """
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user_id
        ).first()
        
        if not subscription:
            subscription = Subscription(
                user_id=user_id,
                plan=plan
            )
            db.add(subscription)
            db.commit()
            db.refresh(subscription)
        
        return subscription

