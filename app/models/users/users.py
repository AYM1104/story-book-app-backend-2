from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database.supabase_base import SupabaseBase

class Users(SupabaseBase):
    """ユーザーモデル
    
    SupabaseBaseを継承してcreated_atとupdated_atを自動管理
    """
    __tablename__ = "users"

    id = Column(String(255), primary_key=True, index=True, comment="Auth0のユーザーID")
    user_name = Column(String(255), nullable=False, comment="ユーザー名")
    email = Column(String(255), nullable=True, unique=True, comment="メールアドレス（オプショナル）")
    balance = Column(Integer, nullable=False, default=0, comment="クレジット残高")
    # password = Column(String(255), nullable=False, comment="パスワード")  # Supabase認証で管理

    # リレーションシップ
    # upload_images = relationship("UploadImages", back_populates="user")  # 外部キー制約がないため無効化
    children = relationship("Child", back_populates="user")
    storybooks = relationship("StoryBook", back_populates="user")
    credit_ledger = relationship("CreditLedger", back_populates="user")
    subscription = relationship("Subscription", back_populates="user", uselist=False)

