import os
from pathlib import Path

# プロジェクトのルートディレクトリ
BASE_DIR = Path(__file__).resolve().parent.parent

""" 画像アップロード関連の設定 """

# 画像ファイルを保存するディレクトリ（ローカル用、GCS使用時は不要）
UPLOAD_DIR = Path(BASE_DIR, "uploads")

# アップロード可能なファイルサイズの上限
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB

# 許可するファイル形式
ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}

# Vision API関連の設定
VISION_API_ENABLED = os.getenv("VISION_API_ENABLED", "true").lower() == "true"

# Google Cloud Storage関連の設定
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
GCS_CREDENTIALS_PATH = os.getenv("GCS_CREDENTIALS_PATH", "app/secrets/ayu1104-9462987945cd.json")

# ストレージ設定（localまたはgcs）
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "gcs")  # デフォルトはGCS