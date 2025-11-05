from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database.supabase_base import SupabaseBase

class Child(SupabaseBase):
    """子どもプロフィールモデル
    
    requirements.md の Child スキーマ定義に基づく
    - id, user_id, name, birthdate?, color_theme?, created_at
    """
    __tablename__ = "children"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True, comment="子どものID")
    user_id = Column(String(255), ForeignKey("users.id"), nullable=False, comment="ユーザーID（Auth0のユーザーID）")
    name = Column(String(255), nullable=False, comment="子どもの名前")
    birthdate = Column(Date, nullable=True, comment="生年月日（任意）")
    color_theme = Column(String(50), nullable=True, comment="カラーテーマ（任意）")

    # リレーションシップ
    user = relationship("Users", back_populates="children")
    storybooks = relationship("StoryBook", back_populates="child")

