from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Story Book Backend - Simple Version")

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
    return {"message": "Story Book Backend is running!", "status": "success"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "story-book-backend"}
