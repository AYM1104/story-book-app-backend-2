import os
from pathlib import Path

# プロジェクトのルートディレクトリ
BASE_DIR = Path(__file__).resolve().parent.parent


""" 画像アップロード関連の設定 """

# 画像ファイルを保存するディレクトリ
UPLOAD_DIR = Path(BASE_DIR, "uploads")

# アップロード可能なファイルサイズの上限
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB

# 許可するファイル形式
ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}

# Vision API関連の設定
VISION_API_ENABLED = os.getenv("VISION_API_ENABLED", "true").lower() == "true"