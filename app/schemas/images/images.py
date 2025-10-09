from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

# 画像アップロード時に受け取るリクエストスキーマ
class UploadImageRequest(BaseModel):
    user_id: int

# 画像アップロード時に受け取るレスポンススキーマ
class UploadImageResponse(BaseModel):
    id: int
    file_name: str
    file_path: str
    content_type: str
    size_bytes: int
    uploaded_at: datetime  # created_atのエイリアス（フロントエンド互換性のため）
    meta_data: Optional[str] = None  # JSON文字列として扱う
    public_url: Optional[str] = None  # GCSの公開URL（ストレージタイプがGCSの場合）

