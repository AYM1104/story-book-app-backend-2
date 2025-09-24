from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, JSON, Enum, Text
from sqlalchemy.orm import relationship
from app.database.base import Base

class GeneratedStoryBook(Base):
    """生成されたえほんを管理するモデル"""
    
    __tablename__ = "generated_story_books"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    story_plot_id = Column(Integer, ForeignKey("story_plots.id"), nullable=False)  # 元のプロットID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # えほんの基本情報
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    keywords = Column(JSON, nullable=True)
    
    # 生成された物語本文（選択されたテーマのみ）
    story_content = Column(Text, nullable=False)
    
    # 5ページの内容
    page_1 = Column(Text, nullable=False)
    page_2 = Column(Text, nullable=False)
    page_3 = Column(Text, nullable=False)
    page_4 = Column(Text, nullable=False)
    page_5 = Column(Text, nullable=False)
    
    # 生成された画像のURL（生成後に更新）
    page_1_image_url = Column(String(512), nullable=True)
    page_2_image_url = Column(String(512), nullable=True)
    page_3_image_url = Column(String(512), nullable=True)
    page_4_image_url = Column(String(512), nullable=True)
    page_5_image_url = Column(String(512), nullable=True)
    
    # 画像生成の状態管理
    image_generation_status = Column(Enum("pending", "generating", "completed", "failed"), 
                                   nullable=False, default="pending")
    
    # メタデータ
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # リレーションシップ
    story_plot = relationship("StoryPlot", back_populates="generated_storybooks")
    user = relationship("Users", back_populates="generated_storybooks")
