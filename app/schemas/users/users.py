from pydantic import BaseModel, EmailStr
from datetime import datetime

# ユーザー作成時に使うスキーマ
class UserCreate(BaseModel):
    user_name: str
    email: EmailStr
    # password: str  # Supabase認証を使用するため、パスワードは不要

# ユーザー情報取得時に使うスキーマ
class UserRead(BaseModel):
    id: int
    user_name: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True