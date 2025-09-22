from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.users.users import Users
from app.schemas.users.users import UserCreate, UserRead

router = APIRouter(tags=["users"])

# 新規ユーザー登録をするエンドポイント
@router.post("/users", response_model=UserRead)
def create_user(user: UserCreate, db: Session = Depends(get_db)):

    # メールアドレスの重複チェック
    if db.query(Users).filter(Users.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # ユーザーを作成
    new_user = Users(user_name=user.user_name, email=user.email, password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

