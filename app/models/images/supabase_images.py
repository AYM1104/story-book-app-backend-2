from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database.supabase_base import SupabaseBase

class SupabaseUploadImages(SupabaseBase):
    """Supabase用の画像アップロードモデル
    
    既存のUploadImagesモデルと互換性を保ちつつ、
    SupabaseBaseを継承してcreated_atとupdated_atを自動管理
    """
    __tablename__ = "upload_images"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    file_name = Column(String(255), nullable=False, comment="ファイル名")
    file_path = Column(String(512), nullable=False, comment="ファイルパス")
    content_type = Column(String(100), nullable=False, comment="コンテンツタイプ")
    size_bytes = Column(Integer, nullable=False, comment="ファイルサイズ（バイト）")
    user_id = Column(String(255), nullable=False, comment="ユーザーID（Auth0のユーザーID）")
    meta_data = Column(Text, nullable=True, comment="画像解析結果のメタデータ")
    public_url = Column(String(1024), nullable=True, comment="公開URL（GCS等）")

    # リレーションシップ（user_idが文字列型のため、外部キー制約なし）
    # user = relationship("SupabaseUsers", back_populates="upload_images")  # 外部キー制約がないため無効化
    story_settings = relationship("SupabaseStorySetting", back_populates="upload_image")
