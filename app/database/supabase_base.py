from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, DateTime, func
from datetime import datetime
from typing import Any

# Supabase用のベースクラス
class SupabaseBase(DeclarativeBase):
    """Supabase用のベースモデルクラス
    
    すべてのSupabaseモデルが継承するベースクラス
    共通のカラム（created_at, updated_at）を提供
    """
    
    # 作成日時（自動設定）
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False,
        comment="作成日時"
    )
    
    # 更新日時（自動更新）
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新日時"
    )
    
    def to_dict(self) -> dict[str, Any]:
        """モデルを辞書形式に変換"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def update_from_dict(self, data: dict[str, Any]) -> None:
        """辞書からモデルの属性を更新"""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def __repr__(self) -> str:
        """デバッグ用の文字列表現"""
        return f"<{self.__class__.__name__}(id={getattr(self, 'id', 'N/A')})>"
