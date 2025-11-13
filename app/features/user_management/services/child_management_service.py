"""子供管理サービスのビジネスロジック"""
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.child.child import Child
from app.models.story.generated_story_book import StoryBook
from app.features.user_management.schemas.children import ChildCreate, ChildUpdate


class ChildManagementService:
    """子供管理サービスクラス"""
    
    @staticmethod
    def create_child(
        user_id: str,
        child_data: ChildCreate,
        db: Session
    ) -> Child:
        """子供プロフィールを作成
        
        Args:
            user_id: ユーザーID（Auth0のsubクレーム）
            child_data: 子供作成データ
            db: データベースセッション
            
        Returns:
            作成されたChildオブジェクト
            
        Raises:
            HTTPException: バリデーションエラー時
        """
        # 生年月日のバリデーション（未来日付は不可）
        if child_data.birthdate and child_data.birthdate > date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="生年月日は未来の日付にできません"
            )
        
        # 子供プロフィールを作成
        child = Child(
            user_id=user_id,
            name=child_data.name,
            birthdate=child_data.birthdate,
            color_theme=child_data.color_theme
        )
        
        db.add(child)
        db.commit()
        db.refresh(child)
        
        return child
    
    @staticmethod
    def get_child_by_id(
        child_id: int,
        user_id: str,
        db: Session
    ) -> Child:
        """特定の子供プロフィールを取得（所有権チェック付き）
        
        Args:
            child_id: 子供ID
            user_id: ユーザーID（Auth0のsubクレーム）
            db: データベースセッション
            
        Returns:
            Childオブジェクト
            
        Raises:
            HTTPException: 子供が見つからない、または所有権がない場合
        """
        child = db.query(Child).filter(
            Child.id == child_id
        ).first()
        
        if not child:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"子供ID {child_id} が見つかりません"
            )
        
        # 所有権チェック
        if child.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="この子供プロフィールにアクセスする権限がありません"
            )
        
        return child
    
    @staticmethod
    def get_user_children(
        user_id: str,
        db: Session
    ) -> list[Child]:
        """ユーザーの子供一覧を取得
        
        Args:
            user_id: ユーザーID（Auth0のsubクレーム）
            db: データベースセッション
            
        Returns:
            子供プロフィールのリスト
        """
        children = db.query(Child).filter(
            Child.user_id == user_id
        ).order_by(Child.created_at.asc()).all()
        
        return children
    
    @staticmethod
    def update_child(
        child_id: int,
        user_id: str,
        child_data: ChildUpdate,
        db: Session
    ) -> Child:
        """子供プロフィールを更新
        
        Args:
            child_id: 子供ID
            user_id: ユーザーID（Auth0のsubクレーム）
            child_data: 更新データ
            db: データベースセッション
            
        Returns:
            更新されたChildオブジェクト
            
        Raises:
            HTTPException: 子供が見つからない、または所有権がない場合
        """
        # 子供を取得（所有権チェック付き）
        child = ChildManagementService.get_child_by_id(child_id, user_id, db)
        
        # 生年月日のバリデーション（未来日付は不可）
        if child_data.birthdate and child_data.birthdate > date.today():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="生年月日は未来の日付にできません"
            )
        
        # 更新フィールドを適用
        if child_data.name is not None:
            child.name = child_data.name
        if child_data.birthdate is not None:
            child.birthdate = child_data.birthdate
        if child_data.color_theme is not None:
            child.color_theme = child_data.color_theme
        
        db.commit()
        db.refresh(child)
        
        return child
    
    @staticmethod
    def delete_child(
        child_id: int,
        user_id: str,
        db: Session
    ) -> dict:
        """子供プロフィールを削除
        
        関連するStoryBookのchild_idをnullに設定してから削除します。
        
        Args:
            child_id: 子供ID
            user_id: ユーザーID（Auth0のsubクレーム）
            db: データベースセッション
            
        Returns:
            削除結果の辞書
            
        Raises:
            HTTPException: 子供が見つからない、または所有権がない場合
        """
        # 子供を取得（所有権チェック付き）
        child = ChildManagementService.get_child_by_id(child_id, user_id, db)
        
        # 関連するStoryBookのchild_idをnullに設定
        related_storybooks = db.query(StoryBook).filter(
            StoryBook.child_id == child_id
        ).all()
        
        for storybook in related_storybooks:
            storybook.child_id = None
        
        # 子供プロフィールを削除
        db.delete(child)
        db.commit()
        
        return {
            "message": "子供プロフィールを削除しました",
            "child_id": child_id,
            "updated_storybooks": len(related_storybooks)
        }


# シングルトンインスタンス
child_management_service = ChildManagementService()

