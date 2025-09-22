from sqlalchemy import Column, Integer, String, JSON, Enum, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database.base import Base

class StorySetting(Base):
    __tablename__ = "story_settings"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    upload_image_id = Column(Integer, ForeignKey("upload_images.id"), nullable=False)

    title_suggestion = Column(String(255), nullable=True)   # 物語のタイトルの提案
    protagonist_name = Column(String(100), nullable=True)   # 主人公の名前
    protagonist_type = Column(String(80), nullable=True)   # 主人公の種類（女の子、男の子、動物、ロボットなど）
    setting_place = Column(String(120), nullable=True)   # 物語の舞台となる場所（公園、海、山、宇宙など）
    tone = Column(Enum("gentle", "fun", "adventure", "mystery"), nullable=True)   # 物語の雰囲気（やさしい、楽しい、冒険的、謎解きなど）
    target_age = Column(Enum("preschool", "elementary_low"), nullable=False, default="preschool")   # 対象年齢（幼稚園、小学生低学年）
    language = Column(String(10), nullable=False, default="ja")
    reading_level = Column(String(30), nullable=True)   # 読みやすさのレベル（やさしいひらがな、やさしいカタカナなど）
    style_guideline = Column(JSON, nullable=True)   # 文体や禁止語などのルール

    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    # 画像とのリレーションシップ（クラス名を修正）
    upload_image = relationship("UploadImages", back_populates="story_settings")