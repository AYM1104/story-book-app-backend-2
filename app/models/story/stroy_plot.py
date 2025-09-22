from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, JSON, Enum, Text
from sqlalchemy.orm import relationship
from app.database.base import Base

class StoryPlot(Base):
    
    """ 物語の骨子（プロット）を管理するモデル """

    __tablename__ = "story_plots"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    story_setting_id = Column(Integer, ForeignKey("story_settings.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 物語の基本情報
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)  # テーマの説明文を保存

    # AIが提案した3つのテーマ案
    theme_options = Column(JSON, nullable=True)
    selected_theme = Column(String(255), nullable=True)

    # 選択されたテーマのキーワード
    keywords = Column(JSON, nullable=True)  # 新しく追加

    # 生成された物語本文（3つのテーマ分）
    generated_stories = Column(JSON, nullable=True)

    # 物語の骨子（プロット）5ページ
    page_1 = Column(Text, nullable=True)
    page_2 = Column(Text, nullable=True)
    page_3 = Column(Text, nullable=True)
    page_4 = Column(Text, nullable=True)
    page_5 = Column(Text, nullable=True)

    # 対話の状態管理
    current_page = Column(Integer, nullable=False, default=1)
    conversation_context = Column(JSON, nullable=True)

    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # リレーションシップ
    story_setting = relationship("StorySetting")
    user = relationship("Users")