from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from app.database.supabase_base import SupabaseBase

class SupabaseStoryPlot(SupabaseBase):
    """Supabase用の物語プロットモデル
    
    既存のStoryPlotモデルと互換性を保ちつつ、
    SupabaseBaseを継承してcreated_atとupdated_atを自動管理
    """
    __tablename__ = "story_plots"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    story_setting_id = Column(Integer, ForeignKey("story_settings.id"), nullable=False, comment="物語設定ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="ユーザーID")

    # 物語の基本情報
    title = Column(String(255), nullable=True, comment="物語のタイトル")
    description = Column(Text, nullable=True, comment="テーマの説明文")

    # AIが提案した3つのテーマ案
    theme_options = Column(JSON, nullable=True, comment="テーマ案の情報")
    selected_theme = Column(String(255), nullable=True, comment="選択されたテーマ")

    # 選択されたテーマのキーワード
    keywords = Column(JSON, nullable=True, comment="テーマのキーワード")

    # 生成された物語本文（3つのテーマ分）
    generated_stories = Column(JSON, nullable=True, comment="生成された物語本文")

    # 物語の骨子（プロット）5ページ
    page_1 = Column(Text, nullable=True, comment="1ページ目の内容")
    page_2 = Column(Text, nullable=True, comment="2ページ目の内容")
    page_3 = Column(Text, nullable=True, comment="3ページ目の内容")
    page_4 = Column(Text, nullable=True, comment="4ページ目の内容")
    page_5 = Column(Text, nullable=True, comment="5ページ目の内容")

    # 対話の状態管理
    current_page = Column(Integer, nullable=False, default=1, comment="現在のページ番号")
    conversation_context = Column(JSON, nullable=True, comment="対話のコンテキスト")

    # リレーションシップ（既存モデルと互換性を保つ）
    story_setting = relationship("SupabaseStorySetting")
    user = relationship("SupabaseUsers")
    generated_storybooks = relationship("SupabaseGeneratedStoryBook", back_populates="story_plot")
