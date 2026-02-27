"""
Live Activityトークンモデル

ActivityKit Push Notifications用のプッシュトークンを管理するモデル。
通常のデバイストークン（APNs alert通知用）とは別に、
Live Activity更新専用のトークンを保存する。
"""

from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from app.database.supabase_base import SupabaseBase


class LiveActivityToken(SupabaseBase):
    """Live Activityプッシュトークンモデル
    
    ActivityKit Push Notifications で Live Activity をサーバーから更新するために、
    Activity開始時にActivityKitが発行する一時的なプッシュトークンを保存する。

    Note: created_at / updated_at は SupabaseBase で自動管理
    """
    __tablename__ = "live_activity_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="ユーザーID")
    push_token = Column(String(512), nullable=False, comment="Live Activity用プッシュトークン（Hex文字列）")
    storybook_id = Column(BigInteger, nullable=False, index=True, comment="対象のストーリーブックID")

    # リレーションシップ
    user = relationship("Users")
