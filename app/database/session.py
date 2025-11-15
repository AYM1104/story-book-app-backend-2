from sqlalchemy import create_engine, event
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
        # Supabaseはアイドル接続を切断することがあるため、
        # pool_pre_ping / pool_recycle を有効にして切断済みコネクションを自動的に検知・再接続する
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,   # 接続の健全性チェック
            pool_recycle=300,     # 5分で接続をリサイクル
            echo=False            # SQLログの出力（必要に応じてTrueに変更）
        )
        
        # 接続時にタイムゾーンをJSTに設定するイベントリスナー
        @event.listens_for(engine, "connect")
        def set_timezone(dbapi_conn, connection_record):
            """データベース接続時にタイムゾーンをJSTに設定"""
            cursor = dbapi_conn.cursor()
            cursor.execute("SET timezone = 'Asia/Tokyo'")
            cursor.close()
        
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
