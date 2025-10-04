from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.database.supabase_base import SupabaseBase

class SupabaseUsers(SupabaseBase):
    """Supabase用のユーザーモデル
    
    既存のUsersモデルと互換性を保ちつつ、
    SupabaseBaseを継承してcreated_atとupdated_atを自動管理
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_name = Column(String(255), nullable=False, comment="ユーザー名")
    email = Column(String(255), nullable=False, unique=True, comment="メールアドレス")
    # password = Column(String(255), nullable=False, comment="パスワード")  # Supabase認証で管理

    # リレーションシップ（既存モデルと互換性を保つ）
    upload_images = relationship("SupabaseUploadImages", back_populates="user")
    generated_storybooks = relationship("SupabaseGeneratedStoryBook", back_populates="user")
