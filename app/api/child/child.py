from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.supabase_session import get_supabase_db
from app.models.child.child import Child
from app.features.user_management.schemas.children import ChildRead, ChildCreate

router = APIRouter(prefix="/child", tags=["child"])

# デバッグ用: ルートが正しく登録されているか確認
@router.get("/test")
async def test_child_endpoint():
    """デバッグ用: ルートが正しく登録されているか確認"""
    return {"message": "Child router is working", "status": "ok"}

@router.post("/", response_model=ChildRead)
async def create_child(
    child: ChildCreate,
    db: Session = Depends(get_supabase_db)
):
    """子供のプロフィールを作成するエンドポイント"""
    try:
        new_child = Child(
            user_id=child.user_id,
            name=child.name,
            birthdate=child.birthdate,
            color_theme=child.color_theme
        )
        
        db.add(new_child)
        db.commit()
        db.refresh(new_child)
        
        return new_child
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"子供の作成に失敗しました: {str(e)}"
        )

@router.get("/user/{user_id}", response_model=list[ChildRead])
async def get_user_children(
    user_id: str,
    db: Session = Depends(get_supabase_db)
):
    """ユーザーの子供一覧を取得するエンドポイント
    
    Args:
        user_id: ユーザーID（Auth0のユーザーID）
        db: データベースセッション
        
    Returns:
        ユーザーの子供プロフィール一覧
    """
    try:
        children = db.query(Child).filter(
            Child.user_id == user_id
        ).order_by(Child.created_at.asc()).all()
        
        return children
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"子供一覧の取得に失敗しました: {str(e)}"
        )

@router.get("/user/{user_id}/count")
async def get_user_children_count(
    user_id: str,
    db: Session = Depends(get_supabase_db)
):
    """ユーザーの子供の人数を取得するエンドポイント
    
    Args:
        user_id: ユーザーID（Auth0のユーザーID）
        db: データベースセッション
        
    Returns:
        dict: 子供の人数情報
            - user_id: ユーザーID
            - children_count: 子供の人数
    """
    try:
        count = db.query(Child).filter(
            Child.user_id == user_id
        ).count()
        
        return {
            "user_id": user_id,
            "children_count": count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"子供の人数取得に失敗しました: {str(e)}"
        )

