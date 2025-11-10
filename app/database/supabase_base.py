from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, DateTime, event, text
from datetime import datetime, timezone, timedelta
from typing import Any

# 日本時間（JST）のタイムゾーンオフセット（UTC+9）
JST = timezone(timedelta(hours=9))

def get_jst_now() -> datetime:
    """現在時刻を日本時間（JST）で取得"""
    # UTC時刻を取得してからJSTに変換することで、システムのタイムゾーンに依存しない
    return datetime.now(timezone.utc).astimezone(JST)

# Supabase用のベースクラス
class SupabaseBase(DeclarativeBase):
    """Supabase用のベースモデルクラス
    
    すべてのSupabaseモデルが継承するベースクラス
    共通のカラム（created_at, updated_at）を提供
    日時は日本時間（JST）で保存されます
    """
    
    # 作成日時（自動設定、日本時間）
    # Supabase経由の直接挿入にも対応するため、サーバーデフォルトでもJSTを設定
    created_at = Column(
        DateTime(timezone=True), 
        nullable=False,
        comment="作成日時（日本時間）",
        server_default=text("timezone('Asia/Tokyo', now())")
    )
    
    # 更新日時（自動更新、日本時間）
    # Supabase経由の直接挿入にも対応するため、サーバーデフォルトでもJSTを設定
    updated_at = Column(
        DateTime(timezone=True), 
        nullable=False,
        comment="更新日時（日本時間）",
        server_default=text("timezone('Asia/Tokyo', now())")
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


# イベントリスナー：インサート時にcreated_atとupdated_atをJSTで設定
@event.listens_for(SupabaseBase, "before_insert", propagate=True)
def receive_before_insert(mapper, connection, target):
    """インサート前にcreated_atとupdated_atをJSTで設定"""
    jst_now = get_jst_now()
    # created_atとupdated_atを常にJST時刻で設定（Noneチェックは不要）
    if hasattr(target, 'created_at'):
        target.created_at = jst_now
    if hasattr(target, 'updated_at'):
        target.updated_at = jst_now


# イベントリスナー：アップデート時にupdated_atをJSTで設定
@event.listens_for(SupabaseBase, "before_update", propagate=True)
def receive_before_update(mapper, connection, target):
    """アップデート前にupdated_atをJSTで設定"""
    if hasattr(target, 'updated_at'):
        target.updated_at = get_jst_now()
