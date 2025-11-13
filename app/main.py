from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import traceback
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# すべてのモデルをインポートしてSQLAlchemyに認識させる
# Supabaseを使用しているため、従来のSQLAlchemyモデルのインポートは不要
# from app.models import *

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
        "message": "ehonnotane Backend is running!", 
        "status": "success",
        "version": "progressive"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "ehonnotane-backend"}

@app.get("/env-check")
def env_check():
    """環境変数の確認用エンドポイント"""
    env_vars = {
        "SUPABASE_URL": bool(os.getenv("SUPABASE_URL")),
        "SUPABASE_ANON_KEY": bool(os.getenv("SUPABASE_ANON_KEY")),
        "SUPABASE_DB_URL": bool(os.getenv("SUPABASE_DB_URL")),
        "GOOGLE_API_KEY_Free": bool(os.getenv("GOOGLE_API_KEY_Free")),
        "GOOGLE_API_KEY_Paid": bool(os.getenv("GOOGLE_API_KEY_Paid")),
        "GOOGLE_CLOUD_PROJECT": bool(os.getenv("GOOGLE_CLOUD_PROJECT")),
        "GCS_BUCKET_NAME": bool(os.getenv("GCS_BUCKET_NAME")),
        "STORAGE_TYPE": os.getenv("STORAGE_TYPE", "not_set"),
        "VISION_API_ENABLED": os.getenv("VISION_API_ENABLED", "not_set"),
        "GOOGLE_APPLICATION_CREDENTIALS_JSON": bool(os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")),
        "GOOGLE_APPLICATION_CREDENTIALS": os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "not_set"),
        # Auth0関連の環境変数
        "AUTH0_DOMAIN": bool(os.getenv("AUTH0_DOMAIN")),
        "AUTH0_API_AUDIENCE": bool(os.getenv("AUTH0_API_AUDIENCE")),
        "AUTH0_NATIVE_CLIENT_ID": bool(os.getenv("AUTH0_NATIVE_CLIENT_ID")),
        "AUTH0_MANAGEMENT_CLIENT_ID": bool(os.getenv("AUTH0_MANAGEMENT_CLIENT_ID")),
        "AUTH0_MANAGEMENT_CLIENT_SECRET": bool(os.getenv("AUTH0_MANAGEMENT_CLIENT_SECRET"))
    }
    return {"environment_variables": env_vars}

# Auth0認証ルーター
try:
    from app.features._00_auth.api.auth0_auth import router as auth0_router
    app.include_router(auth0_router)
    print("✅ Auth0 router loaded successfully")
    # デバッグ: ルーターのパスを確認
    print(f"🔍 Auth0 router prefix: {auth0_router.prefix}")
    print(f"🔍 Auth0 router routes: {[r.path for r in auth0_router.routes]}")
except Exception as e:
    print(f"❌ Failed to load auth0_router: {e}")
    import traceback
    traceback.print_exc()

# Supabaseの基本機能を追加
try:
    from app.api.users.users import router as supabase_users_router
    app.include_router(supabase_users_router, prefix="/api")
    print("✅ Supabase users router loaded successfully")
except Exception as e:
    print(f"❌ Failed to load supabase_users_router: {e}")
    @app.get("/api/users/test")
    def users_test():
        return {"message": "Users router not available", "error": str(e)}

try:
    from app.api.story.questions import router as story_questions_router
    app.include_router(story_questions_router)
    print("✅ Story questions router loaded successfully")
except Exception as e:
    print(f"❌ Failed to load supabase_story_questions_router: {e}")
    @app.get("/api/story/questions/test")
    def story_questions_test():
        return {"message": "Story questions router not available", "error": str(e)}

try:
    from app.features._05_storybook_creation.api.story_generator import router as story_generator_router
    app.include_router(story_generator_router)
    print("✅ Story generator router loaded successfully")
except Exception as e:
    print(f"❌ Failed to load story_generator_router: {e}")
    @app.get("/api/story/generator/test")
    def story_generator_test():
        return {"message": "Story generator router not available", "error": str(e)}

# Supabase版の画像アップロードルーター（無効化）
# try:
#     from app.api.images.supabase_upload_images import router as supabase_images_router
#     app.include_router(supabase_images_router)
#     print("✅ Supabase images router loaded successfully")
# except Exception as e:
#     print(f"❌ Failed to load supabase_images_router: {e}")
#     @app.get("/api/images/test")
#     def images_test():
#         return {"message": "Images router not available", "error": str(e)}

# 従来のGCSアップロードルーター（フロントエンド用）
try:
    from app.features._01_image_upload.api.upload_images import router as upload_images_router
    app.include_router(upload_images_router)
    print("✅ Upload images router loaded successfully")
except Exception as e:
    print(f"❌ Failed to load upload_images_router: {e}")
    @app.get("/api/images/upload/test")
    def upload_images_test():
        return {"message": "Upload images router not available", "error": str(e)}

try:
    from app.api.images.image_generation import router as image_generation_router
    app.include_router(image_generation_router)
    print("✅ Image generation router loaded successfully")
except Exception as e:
    print(f"❌ Failed to load image_generation_router: {e}")
    @app.get("/api/images/generation/test")
    def image_generation_test():
        return {"message": "Image generation router not available", "error": str(e)}

try:
    from app.api.images.image_proxy import router as image_proxy_router
    app.include_router(image_proxy_router)
    print("✅ Image proxy router loaded successfully")
except Exception as e:
    print(f"❌ Failed to load image_proxy_router: {e}")
    @app.get("/api/images/proxy/test")
    def image_proxy_test():
        return {"message": "Image proxy router not available", "error": str(e)}

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
    from app.api.story.supabase_story_book import router as supabase_generated_storybook_router
    app.include_router(supabase_generated_storybook_router, prefix="/api")
    print("✅ Supabase generated storybook router loaded successfully")
except Exception as e:
    print(f"❌ Failed to load supabase_generated_storybook_router: {e}")
    @app.get("/api/storybook/test")
    def storybook_test():
        return {"message": "Generated storybook router not available", "error": str(e)}

# クレジット管理API
try:
    from app.api.credits import router as credits_router
    app.include_router(credits_router, prefix="/api")
    print("✅ Credits router loaded successfully")
except Exception as e:
    print(f"❌ Failed to load credits_router: {e}")
    @app.get("/api/credits/test")
    def credits_test():
        return {"message": "Credits router not available", "error": str(e)}

# 価格見積API
try:
    from app.api.pricing import router as pricing_router
    app.include_router(pricing_router, prefix="/api")
    print("✅ Pricing router loaded successfully")
except Exception as e:
    print(f"❌ Failed to load pricing_router: {e}")
    @app.get("/api/pricing/test")
    def pricing_test():
        return {"message": "Pricing router not available", "error": str(e)}

# 子供管理API
try:
    from app.api.child.child import router as child_router
    app.include_router(child_router, prefix="/api")
    print("✅ Child router loaded successfully")
except Exception as e:
    print(f"❌ Failed to load child_router: {e}")
    @app.get("/api/child/test")
    def child_test():
        return {"message": "Child router not available", "error": str(e)}

# ユーザー管理API（子供管理機能）
try:
    from app.features.user_management.api.children import router as user_management_children_router
    app.include_router(user_management_children_router, prefix="/api")
    print("✅ User management children router loaded successfully")
except Exception as e:
    print(f"❌ Failed to load user_management_children_router: {e}")
    @app.get("/api/user-management/children/test")
    def user_management_children_test():
        return {"message": "User management children router not available", "error": str(e)}

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

@app.get("/debug/auth0-routes")
def debug_auth0_routes():
    """Auth0ルーターのデバッグ情報を表示"""
    try:
        from app.features._00_auth.api.auth0_auth import router as auth0_router
        routes_info = []
        for route in auth0_router.routes:
            if hasattr(route, 'methods') and hasattr(route, 'path'):
                routes_info.append({
                    "path": route.path,
                    "methods": list(route.methods),
                    "full_path": f"{auth0_router.prefix}{route.path}"
                })
        return {
            "router_prefix": auth0_router.prefix,
            "routes": routes_info,
            "is_registered": auth0_router in [r for r in app.routes if hasattr(r, 'prefix')]
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}
