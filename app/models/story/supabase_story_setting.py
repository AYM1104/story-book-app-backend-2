from sqlalchemy import Column, Integer, String, JSON, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.database.supabase_base import SupabaseBase

class SupabaseStorySetting(SupabaseBase):
    """Supabase用の物語設定モデル
    
    既存のStorySettingモデルと互換性を保ちつつ、
    SupabaseBaseを継承してcreated_atとupdated_atを自動管理
    """
    __tablename__ = "story_settings"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    upload_image_id = Column(Integer, ForeignKey("upload_images.id"), nullable=False, comment="アップロード画像ID")

    title_suggestion = Column(String(255), nullable=True, comment="物語のタイトルの提案")
    protagonist_name = Column(String(100), nullable=True, comment="主人公の名前")
    protagonist_type = Column(String(80), nullable=True, comment="主人公の種類（女の子、男の子、動物、ロボットなど）")
    setting_place = Column(String(120), nullable=True, comment="物語の舞台となる場所（公園、海、山、宇宙など）")
    tone = Column(Enum("gentle", "fun", "adventure", "mystery", name="tone_enum"), nullable=True, comment="物語の雰囲気（やさしい、楽しい、冒険的、謎解きなど）")
    target_age = Column(Enum("preschool", "elementary_low", name="target_age_enum"), nullable=False, default="preschool", comment="対象年齢（幼稚園、小学生低学年）")
    language = Column(String(10), nullable=False, default="ja", comment="言語")
    reading_level = Column(String(30), nullable=True, comment="読みやすさのレベル（やさしいひらがな、やさしいカタカナなど）")
    style_guideline = Column(JSON, nullable=True, comment="文体や禁止語などのルール")

    # 画像とのリレーションシップ（既存モデルと互換性を保つ）
    upload_image = relationship("SupabaseUploadImages", back_populates="story_settings")
