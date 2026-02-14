from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class ImageGenerationStatus(str, Enum):
    """画像生成状態のEnum"""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"

# --- ページ関連スキーマ ---

class PageContent(BaseModel):
    """ページ内容（作成・保存用）"""
    page_number: int
    content: str

class PageResponse(BaseModel):
    """ページレスポンス（content + image_url）"""
    page_number: int
    content: str
    image_url: Optional[str] = None

class PageImageUpdate(BaseModel):
    """ページ画像URL更新用"""
    page_number: int
    image_url: str

# --- リクエスト・レスポンス ---

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
    pages: List[PageContent]  # 正規化されたページ配列

class StoryBookResponse(BaseModel):
    """StoryBookレスポンス用スキーマ"""
    id: int
    story_plot_id: int
    user_id: str  # Supabaseでは文字列型（Auth0のユーザーID）
    child_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    keywords: Optional[list] = None
    # worksテーブルから統合した機能
    tags: list[str] = []
    is_favorite: bool = False
    visibility: Dict[str, bool] = {"private": True, "shared": False}
    total_views: int = 0
    # 表紙画像
    cover_image_url: Optional[str] = None
    # 正規化されたページ配列
    pages: List[PageResponse] = []
    # 画像生成状態
    image_generation_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class StorybookImageUrlUpdateRequest(BaseModel):
    """ストーリーブック画像URL更新リクエスト"""
    storybook_id: int
    cover_image_url: Optional[str] = None
    page_images: List[PageImageUpdate] = []  # 正規化されたページ画像配列

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
