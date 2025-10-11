from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# 環境変数からデータベース接続先を取得
# SUPABASE_DB_URLを使用
DATABASE_URL = os.getenv("SUPABASE_DB_URL")

if not DATABASE_URL:
    print("⚠️ データベース接続URLが設定されていません。SUPABASE_DB_URLを設定してください。")
    print("⚠️ データベース機能は利用できません。")
    # ダミーのエンジンとセッションを作成（エラーを回避するため）
    engine = None
    SessionLocal = None
else:
    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        print("✅ データベース接続が正常に設定されました")
    except Exception as e:
        print(f"❌ データベース接続エラー: {e}")
        engine = None
        SessionLocal = None

def get_db():
    if SessionLocal is None:
        raise RuntimeError("データベース接続が設定されていません。SUPABASE_DB_URLを設定してください。")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
