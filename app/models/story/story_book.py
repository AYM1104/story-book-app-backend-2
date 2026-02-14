from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Enum, Text, Boolean, ARRAY
from sqlalchemy.orm import relationship
from app.database.supabase_base import SupabaseBase

class StoryBook(SupabaseBase):
    """えほんモデル（worksテーブルの機能を統合）
    
    SupabaseBaseを継承してcreated_atとupdated_atを自動管理。
    ページデータは StoryPage テーブルで正規化管理。
    """
    __tablename__ = "story_books"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    story_plot_id = Column(Integer, ForeignKey("story_plots.id", ondelete="CASCADE"), nullable=False, comment="元のプロットID")
    user_id = Column(String(255), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="ユーザーID")
    child_id = Column(Integer, ForeignKey("children.id", ondelete="SET NULL"), nullable=True, comment="子どものID（オプショナル）")
    
    # えほんの基本情報
    title = Column(String(255), nullable=False, comment="タイトル")
    description = Column(Text, nullable=True, comment="説明・概要")
    keywords = Column(JSON, nullable=True, comment="キーワード")
    
    # worksテーブルから統合した機能
    tags = Column(ARRAY(String), nullable=False, server_default="{}", comment="タグ配列")
    is_favorite = Column(Boolean, nullable=False, default=False, comment="お気に入りフラグ")
    visibility = Column(JSON, nullable=False, server_default='{"private": true, "shared": false}', comment="公開設定")
    total_views = Column(Integer, nullable=False, default=0, comment="閲覧数")
    
    # 表紙画像URL
    cover_image_url = Column(String(512), nullable=True, comment="表紙の画像URL")
    
    # 画像生成の状態管理
    image_generation_status = Column(Enum("pending", "generating", "completed", "failed", name="image_generation_status_enum"), 
                                   nullable=False, default="pending", comment="画像生成状態")
    generation_progress = Column(JSON, nullable=True, comment="画像生成の詳細進捗情報 {current_page: int, current_step: str, completed_pages: int}")
    
    # リレーションシップ
    story_plot = relationship("StoryPlot", back_populates="storybooks")
    user = relationship("Users", back_populates="storybooks")
    credit_ledger = relationship("CreditLedger", back_populates="work")
    child = relationship("Child", back_populates="storybooks")
    pages = relationship("StoryPage", back_populates="story_book", order_by="StoryPage.page_number", cascade="all, delete-orphan")

