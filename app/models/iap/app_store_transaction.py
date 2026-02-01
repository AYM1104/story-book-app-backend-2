from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database.supabase_base import SupabaseBase

class AppStoreTransaction(SupabaseBase):
    """App Storeトランザクション履歴モデル
    
    App Storeからの全トランザクションを記録し、監査証跡として保持する。
    重複処理の防止にも使用される。
    """
    __tablename__ = "app_store_transactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(String(255), ForeignKey("users.id"), nullable=False, index=True, comment="ユーザーID")
    transaction_id = Column(String(255), unique=True, nullable=False, index=True, comment="トランザクションID（一意）")
    original_transaction_id = Column(String(255), nullable=False, index=True, comment="オリジナルトランザクションID（サブスクリプショングループで共通）")
    product_id = Column(String(255), nullable=False, comment="プロダクトID")
    purchase_date = Column(DateTime(timezone=True), nullable=False, comment="購入日時")
    expires_date = Column(DateTime(timezone=True), nullable=True, comment="有効期限（サブスクリプションの場合）")
    is_upgraded = Column(Boolean, default=False, comment="プランアップグレードフラグ")
    cancellation_date = Column(DateTime(timezone=True), nullable=True, comment="キャンセル日時")
    jws_representation = Column(Text, nullable=True, comment="JWS（JSON Web Signature）- 検証用に保存")
    notification_type = Column(String(100), nullable=True, comment="Server Notificationタイプ（SUBSCRIBED, DID_RENEWなど）")
    
    # リレーションシップ
    user = relationship("Users", back_populates="app_store_transactions")
