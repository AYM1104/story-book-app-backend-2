from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database.base import Base

class UploadImages(Base):
    __tablename__ = "upload_images"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    content_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, nullable=False, default=func.now())
    meta_data = Column(Text, nullable=True)     # 画像解析結果を入れる
    public_url = Column(String(1024), nullable=True)     # GCSの公開URL（ストレージタイプがGCSの場合）

    user = relationship("Users", back_populates="upload_images")
    story_settings = relationship("StorySetting", back_populates="upload_image")