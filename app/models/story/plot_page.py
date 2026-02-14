"""
PlotPage モデル

StoryPlot の各ページのテキスト内容を管理する正規化テーブル。
従来の page_1〜page_10 ハードコードカラムを置き換える。
"""

from sqlalchemy import Column, Integer, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database.supabase_base import SupabaseBase


class PlotPage(SupabaseBase):
    """StoryPlot のページデータ
    
    各ページのテキスト内容を保持する。
    page_number は 1-indexed。
    """
    __tablename__ = "plot_pages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    story_plot_id = Column(
        Integer,
        ForeignKey("story_plots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属する StoryPlot の ID"
    )
    page_number = Column(Integer, nullable=False, comment="ページ番号（1-indexed）")
    content = Column(Text, nullable=False, default="", comment="ページのテキスト内容")

    # リレーション
    story_plot = relationship("StoryPlot", back_populates="pages")

    __table_args__ = (
        UniqueConstraint("story_plot_id", "page_number", name="uq_plot_pages_plot_page"),
    )

    def __repr__(self):
        return f"<PlotPage(id={self.id}, plot={self.story_plot_id}, page={self.page_number})>"
