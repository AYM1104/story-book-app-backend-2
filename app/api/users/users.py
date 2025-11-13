from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.supabase_session import get_supabase_db
from app.models.users.users import Users
from app.schemas.users.users import UserCreate, UserRead
from app.service.credits import CreditsService
from app.models.credits.subscription import PlanType

router = APIRouter(prefix="/users", tags=["users"])

# 新規ユーザー登録をするエンドポイント（Supabase用）
@router.post("/", response_model=UserRead)
def create_supabase_user(user: UserCreate, db: Session = Depends(get_supabase_db)):
    """Supabase用のユーザー作成エンドポイント
    
    初回登録時に300クレジットを付与し、FREEプランを設定します
    """
    
    # メールアドレスの重複チェック
    existing_user = db.query(Users).filter(Users.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # ユーザーIDの重複チェック
    existing_user_by_id = db.query(Users).filter(Users.id == user.id).first()
    if existing_user_by_id:
        raise HTTPException(status_code=400, detail="User ID already registered")
    
    # ユーザーを作成（Auth0のユーザーIDを主キーとして使用）
    new_user = Users(
        id=user.id,  # Auth0のユーザーID
        user_name=user.user_name, 
        email=user.email
        # passwordはSupabase認証で管理されるため不要
    )
    db.add(new_user)
    db.flush()  # IDを取得するためにflush
    
    # 初回登録時の300クレジット付与
    CreditsService.add_credits(
        db=db,
        user_id=user.id,
        amount=300,
        reason="signup_bonus"
    )
    
    # FREEプランのサブスクリプションを作成
    CreditsService.ensure_subscription(
        db=db,
        user_id=user.id,
        plan=PlanType.FREE
    )
    
    db.commit()
    db.refresh(new_user)

    return new_user

# ユーザー一覧取得エンドポイント（Supabase用）
@router.get("/", response_model=list[UserRead])
def get_supabase_users(db: Session = Depends(get_supabase_db)):
    """Supabase用のユーザー一覧取得エンドポイント"""
    
    users = db.query(Users).all()
    # メールアドレスが空文字列の場合、Noneに変換（オプショナルとして扱う）
    # user_nameがNULLまたは空文字列の場合、デフォルト値を設定
    for user in users:
        if not user.email or user.email == "":
            user.email = None
        # user_nameがNULLまたは空文字列の場合、デフォルト値を設定
        if not user.user_name or user.user_name == "":
            # メールアドレスからユーザー名を生成、またはデフォルト値を設定
            if user.email:
                user.user_name = user.email.split("@")[0]
            else:
                user.user_name = f"ユーザー_{user.id[-8:]}"  # IDの最後8文字を使用
    return users

# ユーザー詳細取得エンドポイント（Supabase用）
@router.get("/{user_id}", response_model=UserRead)
def get_supabase_user(user_id: str, db: Session = Depends(get_supabase_db)):
    """Supabase用のユーザー詳細取得エンドポイント"""
    
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # メールアドレスが空文字列の場合、Noneに変換（オプショナルとして扱う）
    if not user.email or user.email == "":
        user.email = None
    
    # user_nameがNULLまたは空文字列の場合、デフォルト値を設定
    if not user.user_name or user.user_name == "":
        # メールアドレスからユーザー名を生成、またはデフォルト値を設定
        if user.email:
            user.user_name = user.email.split("@")[0]
        else:
            user.user_name = f"ユーザー_{user.id[-8:]}"  # IDの最後8文字を使用
    
    return user

# ユーザー削除エンドポイント（Supabase用）
@router.delete("/{user_id}")
def delete_supabase_user(user_id: str, db: Session = Depends(get_supabase_db)):
    """Supabase用のユーザー削除エンドポイント"""
    
    user = db.query(Users).filter(Users.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}

