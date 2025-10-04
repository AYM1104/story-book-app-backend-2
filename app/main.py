from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
# Supabase用APIルーターのみを使用
from app.api.users.supabase_users import router as supabase_users_router
from app.api.images.supabase_upload_images import router as supabase_images_router
from app.api.story.supabase_story_setting import router as supabase_story_setting_router
from app.api.story.supabase_questions import router as supabase_story_questions_router
from app.api.story.supabase_story_generator import router as supabase_story_generator_router
from app.api.story.supabase_generated_story_book import router as supabase_generated_storybook_router
from app.api.images.supabase_image_generation import router as supabase_image_generation_router
from app.api.books.supabase_books_view import router as supabase_books_view_router
from app.database.base import Base
from app.database.session import engine
from dotenv import load_dotenv
from app.core.config import UPLOAD_DIR


load_dotenv()

app = FastAPI()

# データベーステーブルを作成
Base.metadata.create_all(bind=engine)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# アップロード画像の静的配信設定
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# ルートエンドポイント（動作確認用）
@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


""" Supabase用ルーターの設定 """
# ユーザー関連のエンドポイント
app.include_router(supabase_users_router)

# 画像関連のエンドポイント
app.include_router(supabase_images_router)

# 物語設定関連のエンドポイント
app.include_router(supabase_story_setting_router)

# 物語質問関連のエンドポイント
app.include_router(supabase_story_questions_router)

# テーマ生成関連のエンドポイント
app.include_router(supabase_story_generator_router)

# 生成されたストーリーブック関連のエンドポイント
app.include_router(supabase_generated_storybook_router)

# 画像生成関連のエンドポイント
app.include_router(supabase_image_generation_router)

# 絵本ビュー関連のエンドポイント
app.include_router(supabase_books_view_router)
