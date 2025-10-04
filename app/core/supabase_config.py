import os
from pathlib import Path
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# プロジェクトのルートディレクトリ
BASE_DIR = Path(__file__).resolve().parent.parent

""" Supabase関連の設定 """

# Supabase接続設定
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# データベース接続設定（PostgreSQL）
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")  # postgresql://user:password@host:port/database

# ストレージ設定
SUPABASE_STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "storybook-images")

# 認証設定
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

# 画像アップロード関連の設定（Supabase用）
SUPABASE_UPLOAD_DIR = "uploads"  # Supabaseストレージ内のディレクトリ
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}

# 設定の検証
def validate_supabase_config():
    """Supabase設定の検証"""
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
        "SUPABASE_DB_URL"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise ValueError(f"以下の環境変数が設定されていません: {', '.join(missing_vars)}")
    
    return True
