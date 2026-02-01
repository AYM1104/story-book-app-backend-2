from sqlalchemy import Column, Integer, String, Enum
from app.models.credits.subscription import PlanType
from sqlalchemy.orm import relationship
from app.database.supabase_base import SupabaseBase

class Users(SupabaseBase):
    """ ユーザーモデル """
    __tablename__ = "users"

    id = Column(String(255), primary_key=True, index=True, comment="Auth0のユーザーID")
    user_name = Column(String(255), nullable=False, comment="ユーザー名")
    email = Column(String(255), nullable=True, unique=True, comment="メールアドレス（オプショナル）")
    balance = Column(Integer, nullable=False, default=0, comment="クレジット残高")
    subscription_plan = Column(Enum(PlanType), nullable=False, default=PlanType.FREE, comment="現在のサブスクリプションプラン")
    # password = Column(String(255), nullable=False, comment="パスワード")  # Supabase認証で管理

    # リレーションシップ
    children = relationship("Child", back_populates="user")
    storybooks = relationship("StoryBook", back_populates="user")
    credit_ledger = relationship("CreditLedger", back_populates="user")
    subscription = relationship("Subscription", back_populates="user", uselist=False)
    app_store_transactions = relationship("AppStoreTransaction", back_populates="user")
    

