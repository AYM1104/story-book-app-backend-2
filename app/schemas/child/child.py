from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

# 子どもプロフィール作成時に使うスキーマ
class ChildCreate(BaseModel):
    """子どもプロフィール作成リクエストスキーマ
    
    requirements.md の Child スキーマ定義に基づく
    - user_id: Auth0のユーザーID（通常は認証から取得）
    - name: 子どもの名前（必須）
    - birthdate: 生年月日（任意）
    - color_theme: カラーテーマ（任意）
    """
    name: str
    birthdate: Optional[date] = None
    color_theme: Optional[str] = None

# 子どもプロフィール更新時に使うスキーマ
class ChildUpdate(BaseModel):
    """子どもプロフィール更新リクエストスキーマ"""
    name: Optional[str] = None
    birthdate: Optional[date] = None
    color_theme: Optional[str] = None

# 子どもプロフィール情報取得時に使うスキーマ
class ChildRead(BaseModel):
    """子どもプロフィール読み取りレスポンススキーマ
    
    requirements.md の Child スキーマ定義に基づく
    - id, user_id, name, birthdate?, color_theme?, created_at
    """
    id: int
    user_id: str  # Auth0のユーザーID
    name: str
    birthdate: Optional[date] = None
    color_theme: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

