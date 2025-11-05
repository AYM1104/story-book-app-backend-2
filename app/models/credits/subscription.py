from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
from app.database.supabase_base import SupabaseBase
import enum

class PlanType(str, enum.Enum):
    """プランタイプ"""
    FREE = "FREE"  # 無料（登録特典）
    STARTER = "STARTER"  # はじめてのたね
    PLUS = "PLUS"  # そだてるたね
    PREMIUM = "PREMIUM"  # わくわくのたね

class Subscription(SupabaseBase):
    """サブスクリプションモデル
    
    ユーザーのプラン情報を管理する
    SupabaseBaseを継承してcreated_atとupdated_atを自動管理
    """
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(String(255), ForeignKey("users.id"), nullable=False, unique=True, index=True, comment="ユーザーID（1ユーザー1プラン）")
    plan = Column(Enum(PlanType), nullable=False, default=PlanType.FREE, comment="プランタイプ")
    cycle_started_at = Column(DateTime(timezone=True), nullable=True, comment="現在のサイクル開始日時")
    cycle_ends_at = Column(DateTime(timezone=True), nullable=True, comment="現在のサイクル終了日時")
    next_credit_refill_at = Column(DateTime(timezone=True), nullable=True, comment="次回クレジット付与日時")

    # リレーションシップ
    user = relationship("Users", back_populates="subscription")

