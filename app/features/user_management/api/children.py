"""子供管理APIエンドポイント"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.security.auth0_jwt import get_auth0_sub_from_token
from app.database.supabase_session import get_supabase_db
from app.features.user_management.schemas.children import ChildCreate, ChildUpdate, ChildRead
from app.features.user_management.services.child_management_service import child_management_service


router = APIRouter(prefix="/user-management/children", tags=["user-management"])


@router.post("/", response_model=ChildRead, status_code=status.HTTP_201_CREATED)
def create_child(
    child_data: ChildCreate,
    user_id: str = Depends(get_auth0_sub_from_token),
    db: Session = Depends(get_supabase_db)
):
    """子供プロフィールを新規作成
    
    Args:
        child_data: 子供作成データ
        user_id: 認証済みユーザーID（Auth0のsubクレーム、自動取得）
        db: データベースセッション
        
    Returns:
        作成された子供プロフィール情報
        
    Raises:
        HTTPException: バリデーションエラー時
    """
    try:
        child = child_management_service.create_child(
            user_id=user_id,
            child_data=child_data,
            db=db
        )
        return child
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"子供プロフィールの作成に失敗しました: {str(e)}"
        )


@router.get("/", response_model=List[ChildRead])
def get_children(
    user_id: str = Depends(get_auth0_sub_from_token),
    db: Session = Depends(get_supabase_db)
):
    """自分の子供一覧を取得
    
    Args:
        user_id: 認証済みユーザーID（Auth0のsubクレーム、自動取得）
        db: データベースセッション
        
    Returns:
        子供プロフィールのリスト
    """
    try:
        children = child_management_service.get_user_children(
            user_id=user_id,
            db=db
        )
        return children
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"子供一覧の取得に失敗しました: {str(e)}"
        )


@router.get("/{child_id}", response_model=ChildRead)
def get_child(
    child_id: int,
    user_id: str = Depends(get_auth0_sub_from_token),
    db: Session = Depends(get_supabase_db)
):
    """特定の子供プロフィール情報を取得
    
    Args:
        child_id: 子供ID
        user_id: 認証済みユーザーID（Auth0のsubクレーム、自動取得）
        db: データベースセッション
        
    Returns:
        子供プロフィール情報
        
    Raises:
        HTTPException: 子供が見つからない、または所有権がない場合
    """
    try:
        child = child_management_service.get_child_by_id(
            child_id=child_id,
            user_id=user_id,
            db=db
        )
        return child
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"子供プロフィールの取得に失敗しました: {str(e)}"
        )


@router.put("/{child_id}", response_model=ChildRead)
def update_child(
    child_id: int,
    child_data: ChildUpdate,
    user_id: str = Depends(get_auth0_sub_from_token),
    db: Session = Depends(get_supabase_db)
):
    """子供プロフィール情報を更新
    
    Args:
        child_id: 子供ID
        child_data: 更新データ（部分更新可能）
        user_id: 認証済みユーザーID（Auth0のsubクレーム、自動取得）
        db: データベースセッション
        
    Returns:
        更新された子供プロフィール情報
        
    Raises:
        HTTPException: 子供が見つからない、所有権がない、またはバリデーションエラー時
    """
    try:
        child = child_management_service.update_child(
            child_id=child_id,
            user_id=user_id,
            child_data=child_data,
            db=db
        )
        return child
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"子供プロフィールの更新に失敗しました: {str(e)}"
        )


@router.delete("/{child_id}", status_code=status.HTTP_200_OK)
def delete_child(
    child_id: int,
    user_id: str = Depends(get_auth0_sub_from_token),
    db: Session = Depends(get_supabase_db)
):
    """子供プロフィールを削除
    
    関連するStoryBookのchild_idをnullに設定してから削除します。
    
    Args:
        child_id: 子供ID
        user_id: 認証済みユーザーID（Auth0のsubクレーム、自動取得）
        db: データベースセッション
        
    Returns:
        削除結果
        
    Raises:
        HTTPException: 子供が見つからない、または所有権がない場合
    """
    try:
        result = child_management_service.delete_child(
            child_id=child_id,
            user_id=user_id,
            db=db
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"子供プロフィールの削除に失敗しました: {str(e)}"
        )

