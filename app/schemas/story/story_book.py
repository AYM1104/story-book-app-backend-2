from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ImageGenerationStatus(str, Enum):
    """画像生成状態のEnum"""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"

class ThemeConfirmationRequest(BaseModel):
    """テーマ選択確認リクエスト"""
    story_plot_id: int
    selected_theme: str
    child_id: Optional[int] = None  # 子どものID（オプショナル）
    story_pages: int  # 物語ページ数（3, 5, 7, 10のいずれか）

class StoryBookCreate(BaseModel):
    """StoryBook作成用スキーマ"""
    story_plot_id: int
    title: str
    description: Optional[str] = None
    keywords: Optional[list] = None
    story_content: str
    page_1: str
    page_2: str
    page_3: str
    page_4: str
    page_5: str
    page_6: Optional[str] = None
    page_7: Optional[str] = None
    page_8: Optional[str] = None
    page_9: Optional[str] = None
    page_10: Optional[str] = None

class StoryBookResponse(BaseModel):
    """StoryBookレスポンス用スキーマ（worksテーブルの機能を統合）"""
    id: int
    story_plot_id: int
    user_id: str  # Supabaseでは文字列型（Auth0のユーザーID）
    child_id: Optional[int]
    title: str
    description: Optional[str] = None
    keywords: Optional[list] = None
    # worksテーブルから統合した機能
    tags: list[str] = []
    is_favorite: bool = False
    visibility: Dict[str, bool] = {"private": True, "shared": False}
    total_views: int = 0
    story_content: str
    page_1: str
    page_2: str
    page_3: str
    page_4: str
    page_5: str
    page_6: Optional[str] = None
    page_7: Optional[str] = None
    page_8: Optional[str] = None
    page_9: Optional[str] = None
    page_10: Optional[str] = None
    cover_image_url: Optional[str] = None
    page_1_image_url: Optional[str] = None
    page_2_image_url: Optional[str] = None
    page_3_image_url: Optional[str] = None
    page_4_image_url: Optional[str] = None
    page_5_image_url: Optional[str] = None
    page_6_image_url: Optional[str] = None
    page_7_image_url: Optional[str] = None
    page_8_image_url: Optional[str] = None
    page_9_image_url: Optional[str] = None
    page_10_image_url: Optional[str] = None
    image_generation_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class StorybookImageUrlUpdateRequest(BaseModel):
    """ストーリーブック画像URL更新リクエスト"""
    storybook_id: int
    cover_image_url: Optional[str] = None
    page_1_image_url: Optional[str] = None
    page_2_image_url: Optional[str] = None
    page_3_image_url: Optional[str] = None
    page_4_image_url: Optional[str] = None
    page_5_image_url: Optional[str] = None
    page_6_image_url: Optional[str] = None
    page_7_image_url: Optional[str] = None
    page_8_image_url: Optional[str] = None
    page_9_image_url: Optional[str] = None
    page_10_image_url: Optional[str] = None

class StorybookImageUrlUpdateResponse(BaseModel):
    """ストーリーブック画像URL更新レスポンス"""
    success: bool
    message: str
    storybook_id: int
    updated_pages: list[str]

class ThemeConfirmationResponse(BaseModel):
    """テーマ確認レスポンス"""
    success: bool
    message: str
    storybook_id: int
    selected_theme: str
