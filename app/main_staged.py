from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

app = FastAPI(title="Story Book Backend - Staged Version")

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルートエンドポイント（動作確認用）
@app.get("/")
def read_root():
    return {
        "message": "Story Book Backend is running!", 
        "status": "success",
        "version": "staged"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "story-book-backend"}

@app.get("/env-check")
def env_check():
    """環境変数の確認用エンドポイント"""
    env_vars = {
        "SUPABASE_URL": bool(os.getenv("SUPABASE_URL")),
        "SUPABASE_ANON_KEY": bool(os.getenv("SUPABASE_ANON_KEY")),
        "SUPABASE_DB_URL": bool(os.getenv("SUPABASE_DB_URL")),
        "GOOGLE_API_KEY": bool(os.getenv("GOOGLE_API_KEY")),
        "GCS_BUCKET_NAME": bool(os.getenv("GCS_BUCKET_NAME")),
        "STORAGE_TYPE": os.getenv("STORAGE_TYPE", "not_set"),
        "VISION_API_ENABLED": os.getenv("VISION_API_ENABLED", "not_set")
    }
    return {"environment_variables": env_vars}

# 段階的に機能を追加していく予定
# TODO: Supabase関連のエンドポイントを追加
# TODO: 画像アップロード機能を追加
# TODO: ストーリー生成機能を追加
