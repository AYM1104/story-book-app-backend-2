from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Enum, Text, Boolean, ARRAY
from sqlalchemy.orm import relationship
from app.database.supabase_base import SupabaseBase

class StoryBook(SupabaseBase):
    """えほんモデル（worksテーブルの機能を統合）
    
    SupabaseBaseを継承してcreated_atとupdated_atを自動管理
    """
    __tablename__ = "story_books"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    story_plot_id = Column(Integer, ForeignKey("story_plots.id"), nullable=False, comment="元のプロットID")
    user_id = Column(String(255), ForeignKey("users.id"), nullable=False, comment="ユーザーID")
    child_id = Column(Integer, ForeignKey("children.id"), nullable=True, comment="子どものID（オプショナル）")
    
    # えほんの基本情報
    title = Column(String(255), nullable=False, comment="タイトル")
    description = Column(Text, nullable=True, comment="説明・概要")
    keywords = Column(JSON, nullable=True, comment="キーワード")
    
    # worksテーブルから統合した機能
    tags = Column(ARRAY(String), nullable=False, server_default="{}", comment="タグ配列")
    is_favorite = Column(Boolean, nullable=False, default=False, comment="お気に入りフラグ")
    visibility = Column(JSON, nullable=False, server_default='{"private": true, "shared": false}', comment="公開設定")
    total_views = Column(Integer, nullable=False, default=0, comment="閲覧数")
    
    # 生成された物語本文（選択されたテーマのみ）
    content = Column(Text, nullable=False, comment="物語本文（メイン）")
    story_content = Column(Text, nullable=True, comment="物語本文（詳細）")
    
    # 最大10ページの内容
    page_1 = Column(Text, nullable=False, comment="1ページ目の内容")
    page_2 = Column(Text, nullable=False, comment="2ページ目の内容")
    page_3 = Column(Text, nullable=False, comment="3ページ目の内容")
    page_4 = Column(Text, nullable=False, comment="4ページ目の内容")
    page_5 = Column(Text, nullable=False, comment="5ページ目の内容")
    page_6 = Column(Text, nullable=True, comment="6ページ目の内容")
    page_7 = Column(Text, nullable=True, comment="7ページ目の内容")
    page_8 = Column(Text, nullable=True, comment="8ページ目の内容")
    page_9 = Column(Text, nullable=True, comment="9ページ目の内容")
    page_10 = Column(Text, nullable=True, comment="10ページ目の内容")
    
    # 生成された画像のURL（生成後に更新）
    cover_image_url = Column(String(512), nullable=True, comment="表紙の画像URL")
    page_1_image_url = Column(String(512), nullable=True, comment="1ページ目の画像URL")
    page_2_image_url = Column(String(512), nullable=True, comment="2ページ目の画像URL")
    page_3_image_url = Column(String(512), nullable=True, comment="3ページ目の画像URL")
    page_4_image_url = Column(String(512), nullable=True, comment="4ページ目の画像URL")
    page_5_image_url = Column(String(512), nullable=True, comment="5ページ目の画像URL")
    page_6_image_url = Column(String(512), nullable=True, comment="6ページ目の画像URL")
    page_7_image_url = Column(String(512), nullable=True, comment="7ページ目の画像URL")
    page_8_image_url = Column(String(512), nullable=True, comment="8ページ目の画像URL")
    page_9_image_url = Column(String(512), nullable=True, comment="9ページ目の画像URL")
    page_10_image_url = Column(String(512), nullable=True, comment="10ページ目の画像URL")
    
    # 画像生成の状態管理
    image_generation_status = Column(Enum("pending", "generating", "completed", "failed", name="image_generation_status_enum"), 
                                   nullable=False, default="pending", comment="画像生成状態")
    
    # リレーションシップ
    story_plot = relationship("StoryPlot", back_populates="storybooks")
    user = relationship("Users", back_populates="storybooks")
    credit_ledger = relationship("CreditLedger", back_populates="work")
    child = relationship("Child", back_populates="storybooks")
