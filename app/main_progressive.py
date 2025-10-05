from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# すべてのモデルをインポートしてSQLAlchemyに認識させる
from app.models import *

app = FastAPI(title="Story Book Backend - Progressive Version")

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
        "version": "progressive"
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
        "VISION_API_ENABLED": os.getenv("VISION_API_ENABLED", "not_set"),
        "GOOGLE_APPLICATION_CREDENTIALS_JSON": bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")),
        "GOOGLE_APPLICATION_CREDENTIALS": os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "not_set")
    }
    return {"environment_variables": env_vars}

# Supabaseの基本機能を追加
try:
    from app.api.users.supabase_users import router as supabase_users_router
    app.include_router(supabase_users_router)
    print("✅ Supabase users router loaded successfully")
except Exception as e:
    print(f"❌ Failed to load supabase_users_router: {e}")
    @app.get("/api/users/test")
    def users_test():
        return {"message": "Users router not available", "error": str(e)}

try:
    from app.api.story.supabase_questions import router as supabase_story_questions_router
    app.include_router(supabase_story_questions_router)
    print("✅ Supabase story questions router loaded successfully")
except Exception as e:
    print(f"❌ Failed to load supabase_story_questions_router: {e}")
    @app.get("/api/story/questions/test")
    def story_questions_test():
        return {"message": "Story questions router not available", "error": str(e)}

try:
    from app.api.story.supabase_story_generator import router as supabase_story_generator_router
    app.include_router(supabase_story_generator_router)
    print("✅ Supabase story generator router loaded successfully")
except Exception as e:
    print(f"❌ Failed to load supabase_story_generator_router: {e}")
    @app.get("/api/story/generator/test")
    def story_generator_test():
        return {"message": "Story generator router not available", "error": str(e)}

try:
    from app.api.images.supabase_upload_images import router as supabase_images_router
    app.include_router(supabase_images_router)
    print("✅ Supabase images router loaded successfully")
except Exception as e:
    print(f"❌ Failed to load supabase_images_router: {e}")
    @app.get("/api/images/test")
    def images_test():
        return {"message": "Images router not available", "error": str(e)}

try:
    from app.api.images.supabase_image_generation import router as supabase_image_generation_router
    app.include_router(supabase_image_generation_router)
    print("✅ Supabase image generation router loaded successfully")
except Exception as e:
    print(f"❌ Failed to load supabase_image_generation_router: {e}")
    @app.get("/api/images/generation/test")
    def image_generation_test():
        return {"message": "Image generation router not available", "error": str(e)}

try:
    from app.api.images.image_generation import router as image_generation_router
    app.include_router(image_generation_router)
    print("✅ Image generation router loaded successfully")
except Exception as e:
    print(f"❌ Failed to load image_generation_router: {e}")
    @app.get("/api/images/generation/fallback-test")
    def image_generation_fallback_test():
        return {"message": "Image generation fallback router not available", "error": str(e)}

try:
    from app.api.story.supabase_story_setting import router as supabase_story_setting_router
    app.include_router(supabase_story_setting_router)
    print("✅ Supabase story setting router loaded successfully")
except Exception as e:
    print(f"❌ Failed to load supabase_story_setting_router: {e}")
    @app.get("/api/story/test")
    def story_test():
        return {"message": "Story router not available", "error": str(e)}

try:
    from app.api.story.supabase_generated_story_book import router as supabase_generated_storybook_router
    app.include_router(supabase_generated_storybook_router)
    print("✅ Supabase generated storybook router loaded successfully")
except Exception as e:
    print(f"❌ Failed to load supabase_generated_storybook_router: {e}")
    @app.get("/api/storybook/test")
    def storybook_test():
        return {"message": "Generated storybook router not available", "error": str(e)}

@app.get("/api/routes")
def list_routes():
    """利用可能なルートの一覧を表示"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods)
            })
    return {"available_routes": routes}
