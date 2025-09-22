from fastapi import FastAPI
from app.api.users.users import router as users_router
from app.api.images.upload_images import router as images_router
from app.api.story.story_setting import router as story_setting_router
from app.api.story.questions import router as story_questions_router
from app.api.story.story_generator import router as story_generator_router
# nanobanana関連のインポートを削除
from app.api.images.image_generation import router as image_generation_router
from app.database.base import Base
from app.database.session import engine
from dotenv import load_dotenv


load_dotenv()

app = FastAPI()

# データベーステーブルを作成
Base.metadata.create_all(bind=engine)

# ルートエンドポイント（動作確認用）
@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


""" ルーターの設定 """
# ユーザー関連のエンドポイント
app.include_router(users_router)

# 画像関連のエンドポイント
app.include_router(images_router)

# 物語設定関連のエンドポイント
app.include_router(story_setting_router)

# 物語質問関連のエンドポイント
app.include_router(story_questions_router)

# テーマ生成関連のエンドポイント
app.include_router(story_generator_router)

# 画像生成関連のエンドポイント
app.include_router(image_generation_router)
