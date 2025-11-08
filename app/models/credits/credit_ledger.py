from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database.supabase_base import SupabaseBase

class CreditLedger(SupabaseBase):
    """クレジット台帳モデル
    
    ユーザーのクレジット変動履歴を記録する

    """
    __tablename__ = "credit_ledger"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(String(255), ForeignKey("users.id"), nullable=False, index=True, comment="ユーザーID")
    delta = Column(Integer, nullable=False, comment="クレジット変動額（正の値=付与、負の値=消費）")
    reason = Column(String(255), nullable=False, comment="変動理由（signup_bonus, story_generated, subscription_refill等）")
    work_id = Column(Integer, ForeignKey("story_books.id"), nullable=True, comment="関連する作品ID（消費時に使用）")

    # リレーションシップ
    user = relationship("Users", back_populates="credit_ledger")
    work = relationship("StoryBook", back_populates="credit_ledger")

