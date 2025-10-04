from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.supabase_config import SUPABASE_DB_URL, validate_supabase_config
import os
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# Supabase設定の検証
try:
    validate_supabase_config()
except ValueError as e:
    print(f"Supabase設定エラー: {e}")
    print("環境変数を確認してください")

# Supabase PostgreSQLデータベースへの接続
engine = create_engine(
    SUPABASE_DB_URL,
    pool_pre_ping=True,  # 接続の健全性チェック
    pool_recycle=300,    # 5分で接続をリサイクル
    echo=False           # SQLログの出力（開発時はTrueに設定可能）
)

# セッションファクトリーの作成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_supabase_db():
    """Supabaseデータベースセッションを取得する依存性注入関数"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_supabase_db_sync():
    """同期版のSupabaseデータベースセッション取得"""
    return SessionLocal()

# データベース接続テスト用の関数
def test_supabase_connection():
    """Supabaseデータベース接続をテスト"""
    try:
        db = SessionLocal()
        # 簡単なクエリで接続をテスト
        from sqlalchemy import text
        result = db.execute(text("SELECT 1"))
        db.close()
        print("Supabaseデータベース接続成功")
        return True
    except Exception as e:
        print(f"Supabaseデータベース接続エラー: {e}")
        return False
