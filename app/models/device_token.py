"""
デバイストークンモデル

プッシュ通知用のデバイストークンを管理するモデル。
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.supabase_base import SupabaseBase


class DeviceToken(SupabaseBase):
    """デバイストークンモデル - プッシュ通知用"""
    __tablename__ = "device_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="ユーザーID")
    device_token = Column(String(512), nullable=False, unique=True, comment="デバイストークン")
    platform = Column(String(20), nullable=False, default="ios", comment="プラットフォーム（ios/android）")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="作成日時")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新日時")

    # リレーションシップ
    user = relationship("Users", back_populates="device_tokens")
