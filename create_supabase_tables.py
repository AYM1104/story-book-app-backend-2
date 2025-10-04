#!/usr/bin/env python3
"""
Supabase用のテーブル作成スクリプト

使用方法:
python create_supabase_tables.py
"""

from app.database.supabase_base import SupabaseBase
from app.database.supabase_session import engine
from app.models.users.supabase_users import SupabaseUsers
from app.models.images.supabase_images import SupabaseUploadImages
from app.models.story.supabase_story_setting import SupabaseStorySetting
from app.models.story.supabase_story_plot import SupabaseStoryPlot
from app.models.story.supabase_generated_story_book import SupabaseGeneratedStoryBook

def create_supabase_tables():
    """Supabase用のテーブルを作成"""
    try:
        print("Supabase用テーブルの作成を開始...")
        
        # テーブルを作成
        SupabaseBase.metadata.create_all(bind=engine)
        
        print("Supabase用テーブルの作成が完了しました")
        print("作成されたテーブル:")
        for table_name in SupabaseBase.metadata.tables.keys():
            print(f"  - {table_name}")
            
    except Exception as e:
        print(f"テーブル作成エラー: {e}")
        return False
    
    return True

def test_supabase_connection():
    """Supabase接続テスト"""
    try:
        from app.database.supabase_session import test_supabase_connection
        return test_supabase_connection()
    except Exception as e:
        print(f"❌ 接続テストエラー: {e}")
        return False

if __name__ == "__main__":
    print("=== Supabaseテーブル作成スクリプト ===")
    
    # 接続テスト
    print("1. Supabase接続テスト...")
    if not test_supabase_connection():
        print("接続テストに失敗しました。環境変数を確認してください。")
        exit(1)
    
    # テーブル作成
    print("2. テーブル作成...")
    if create_supabase_tables():
        print("すべての処理が完了しました！")
    else:
        print("テーブル作成に失敗しました。")
        exit(1)
