"""
StoryPage モデル

StoryBook の各ページのテキスト内容と画像URLを管理する正規化テーブル。
従来の page_1〜page_10 ハードコードカラムを置き換える。
"""

from sqlalchemy import Column, Integer, Text, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database.supabase_base import SupabaseBase


class StoryPage(SupabaseBase):
    """StoryBook のページデータ
    
    各ページのテキスト内容と画像URLを保持する。
    page_number は 1-indexed。
    """
    __tablename__ = "story_pages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    story_book_id = Column(
        Integer,
        ForeignKey("story_books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属する StoryBook の ID"
    )
    page_number = Column(Integer, nullable=False, comment="ページ番号（1-indexed）")
    content = Column(Text, nullable=False, default="", comment="ページのテキスト内容")
    image_url = Column(String(512), nullable=True, comment="ページの画像URL")

    # リレーション
    story_book = relationship("StoryBook", back_populates="pages")

    __table_args__ = (
        UniqueConstraint("story_book_id", "page_number", name="uq_story_pages_book_page"),
    )

    def __repr__(self):
        return f"<StoryPage(id={self.id}, book={self.story_book_id}, page={self.page_number})>"
