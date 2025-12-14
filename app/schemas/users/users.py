from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from app.models.credits.subscription import PlanType

# ユーザー作成時に使うスキーマ
class UserCreate(BaseModel):
    id: str  # Auth0のユーザーID
    user_name: str
    email: EmailStr
    # password: str  # Supabase認証を使用するため、パスワードは不要

# ユーザー更新時に使うスキーマ
class UserUpdate(BaseModel):
    user_name: Optional[str] = None
    email: Optional[EmailStr] = None

# ユーザー情報取得時に使うスキーマ
class UserRead(BaseModel):
    id: str  # Auth0のユーザーID
    user_name: str
    email: Optional[EmailStr] = None  # メールアドレス（オプショナル）
    balance: int  # クレジット残高
    subscription_plan: PlanType  # サブスクリプションプラン
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True