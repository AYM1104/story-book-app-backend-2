#!/usr/bin/env python3
"""データベースのタイムゾーン設定を確認するスクリプト"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from datetime import datetime, timezone, timedelta

# プロジェクトのルートディレクトリをパスに追加
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# 環境変数を読み込み
load_dotenv()

# Supabase設定をインポート
from app.core.supabase_config import SUPABASE_DB_URL

# JSTのタイムゾーンオフセット
JST = timezone(timedelta(hours=9))

def check_database_timezone():
    """データベースのタイムゾーン設定を確認"""
    try:
        # データベース接続
        engine = create_engine(SUPABASE_DB_URL)
        
        with engine.connect() as conn:
            print("=" * 60)
            print("データベースタイムゾーン設定の確認")
            print("=" * 60)
            print()
            
            # 1. データベースのデフォルトタイムゾーンを確認
            result = conn.execute(text("SHOW timezone"))
            db_timezone = result.scalar()
            print(f"1. データベースのデフォルトタイムゾーン: {db_timezone}")
            print()
            
            # 2. 現在のセッションのタイムゾーンを確認
            result = conn.execute(text("SELECT current_setting('timezone')"))
            session_timezone = result.scalar()
            print(f"2. 現在のセッションのタイムゾーン: {session_timezone}")
            print()
            
            # 3. 現在時刻を様々な形式で取得
            print("3. 現在時刻の確認:")
            
            # UTC時刻
            result = conn.execute(text("SELECT now() AT TIME ZONE 'UTC'"))
            utc_now = result.scalar()
            print(f"   UTC時刻: {utc_now}")
            
            # JST時刻
            result = conn.execute(text("SELECT now() AT TIME ZONE 'Asia/Tokyo'"))
            jst_now = result.scalar()
            print(f"   JST時刻: {jst_now}")
            
            # タイムゾーン設定後の現在時刻
            conn.execute(text("SET timezone = 'Asia/Tokyo'"))
            result = conn.execute(text("SELECT now()"))
            jst_now_set = result.scalar()
            print(f"   timezone設定後のnow(): {jst_now_set}")
            print()
            
            # 4. Python側の現在時刻との比較
            print("4. Python側の現在時刻:")
            python_utc = datetime.now(timezone.utc)
            python_jst = datetime.now(JST)
            print(f"   Python UTC: {python_utc}")
            print(f"   Python JST: {python_jst}")
            print()
            
            # 5. タイムゾーン変換のテスト
            print("5. タイムゾーン変換のテスト:")
            result = conn.execute(text("""
                SELECT 
                    now() as current_db_time,
                    now() AT TIME ZONE 'UTC' as utc_time,
                    now() AT TIME ZONE 'Asia/Tokyo' as jst_time,
                    timezone('Asia/Tokyo', now()) as jst_timezone_func
            """))
            row = result.fetchone()
            print(f"   DBのnow(): {row[0]}")
            print(f"   UTC変換: {row[1]}")
            print(f"   JST変換: {row[2]}")
            print(f"   timezone関数: {row[3]}")
            print()
            
            # 6. 実際のテーブルのcreated_atを確認（サンプル）
            print("6. 実際のテーブルのcreated_atを確認（サンプル）:")
            try:
                result = conn.execute(text("""
                    SELECT 
                        id,
                        created_at,
                        created_at AT TIME ZONE 'UTC' as created_at_utc,
                        created_at AT TIME ZONE 'Asia/Tokyo' as created_at_jst
                    FROM users
                    ORDER BY created_at DESC
                    LIMIT 3
                """))
                rows = result.fetchall()
                if rows:
                    for row in rows:
                        print(f"   ID: {row[0]}")
                        print(f"      created_at (DB): {row[1]}")
                        print(f"      created_at (UTC): {row[2]}")
                        print(f"      created_at (JST): {row[3]}")
                        print()
                else:
                    print("   usersテーブルにデータがありません")
            except Exception as e:
                print(f"   usersテーブルの確認でエラー: {e}")
            
            print("=" * 60)
            print("確認完了")
            print("=" * 60)
            
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    check_database_timezone()

