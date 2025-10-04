from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.supabase_session import get_supabase_db
from app.models.users.supabase_users import SupabaseUsers
from app.schemas.users.users import UserCreate, UserRead

router = APIRouter(prefix="/users", tags=["users"])

# 新規ユーザー登録をするエンドポイント（Supabase用）
@router.post("/", response_model=UserRead)
def create_supabase_user(user: UserCreate, db: Session = Depends(get_supabase_db)):
    """Supabase用のユーザー作成エンドポイント"""
    
    # メールアドレスの重複チェック
    existing_user = db.query(SupabaseUsers).filter(SupabaseUsers.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # ユーザーを作成
    new_user = SupabaseUsers(
        user_name=user.user_name, 
        email=user.email
        # passwordはSupabase認証で管理されるため不要
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

# ユーザー一覧取得エンドポイント（Supabase用）
@router.get("/", response_model=list[UserRead])
def get_supabase_users(db: Session = Depends(get_supabase_db)):
    """Supabase用のユーザー一覧取得エンドポイント"""
    
    users = db.query(SupabaseUsers).all()
    return users

# ユーザー詳細取得エンドポイント（Supabase用）
@router.get("/{user_id}", response_model=UserRead)
def get_supabase_user(user_id: int, db: Session = Depends(get_supabase_db)):
    """Supabase用のユーザー詳細取得エンドポイント"""
    
    user = db.query(SupabaseUsers).filter(SupabaseUsers.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

# ユーザー削除エンドポイント（Supabase用）
@router.delete("/{user_id}")
def delete_supabase_user(user_id: int, db: Session = Depends(get_supabase_db)):
    """Supabase用のユーザー削除エンドポイント"""
    
    user = db.query(SupabaseUsers).filter(SupabaseUsers.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}
