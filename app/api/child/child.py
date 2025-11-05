from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.supabase_session import get_supabase_db
from app.models.child.child import Child
from app.schemas.child.child import ChildRead

router = APIRouter(prefix="/child", tags=["child"])

# デバッグ用: ルートが正しく登録されているか確認
@router.get("/test")
async def test_child_endpoint():
    """デバッグ用: ルートが正しく登録されているか確認"""
    return {"message": "Child router is working", "status": "ok"}

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

