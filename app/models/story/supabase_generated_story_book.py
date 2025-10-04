from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Enum, Text
from sqlalchemy.orm import relationship
from app.database.supabase_base import SupabaseBase

class SupabaseGeneratedStoryBook(SupabaseBase):
    """Supabase用の生成されたえほんモデル
    
    既存のGeneratedStoryBookモデルと互換性を保ちつつ、
    SupabaseBaseを継承してcreated_atとupdated_atを自動管理
    """
    __tablename__ = "generated_story_books"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    story_plot_id = Column(Integer, ForeignKey("story_plots.id"), nullable=False, comment="元のプロットID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="ユーザーID")
    
    # えほんの基本情報
    title = Column(String(255), nullable=False, comment="タイトル")
    description = Column(Text, nullable=True, comment="説明")
    keywords = Column(JSON, nullable=True, comment="キーワード")
    
    # 生成された物語本文（選択されたテーマのみ）
    story_content = Column(Text, nullable=False, comment="物語本文")
    
    # 5ページの内容
    page_1 = Column(Text, nullable=False, comment="1ページ目の内容")
    page_2 = Column(Text, nullable=False, comment="2ページ目の内容")
    page_3 = Column(Text, nullable=False, comment="3ページ目の内容")
    page_4 = Column(Text, nullable=False, comment="4ページ目の内容")
    page_5 = Column(Text, nullable=False, comment="5ページ目の内容")
    
    # 生成された画像のURL（生成後に更新）
    page_1_image_url = Column(String(512), nullable=True, comment="1ページ目の画像URL")
    page_2_image_url = Column(String(512), nullable=True, comment="2ページ目の画像URL")
    page_3_image_url = Column(String(512), nullable=True, comment="3ページ目の画像URL")
    page_4_image_url = Column(String(512), nullable=True, comment="4ページ目の画像URL")
    page_5_image_url = Column(String(512), nullable=True, comment="5ページ目の画像URL")
    
    # 画像生成の状態管理
    image_generation_status = Column(Enum("pending", "generating", "completed", "failed", name="image_generation_status_enum"), 
                                   nullable=False, default="pending", comment="画像生成状態")
    
    # リレーションシップ（既存モデルと互換性を保つ）
    story_plot = relationship("SupabaseStoryPlot", back_populates="generated_storybooks")
    user = relationship("SupabaseUsers", back_populates="generated_storybooks")
