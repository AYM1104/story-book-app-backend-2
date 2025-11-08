#!/usr/bin/env python3
"""
upload_imagesテーブルの日時カラムを日本時間（JST）に更新するマイグレーションスクリプト

使用方法:
python migrate_upload_images_timezone.py
"""

from sqlalchemy import text
from app.database.supabase_session import engine, test_supabase_connection


def migrate_upload_images_timezone():
    """upload_imagesテーブルのcreated_atとupdated_atを日本時間に更新"""
    try:
        print("=== upload_imagesテーブルのタイムゾーン更新 ===")
        
        # 接続テスト
        print("1. データベース接続テスト...")
        if not test_supabase_connection():
            print("❌ 接続テストに失敗しました。環境変数を確認してください。")
            return False
        
        # データベース接続を取得
        with engine.connect() as connection:
            # トランザクション開始
            trans = connection.begin()
            
            try:
                print("2. upload_imagesテーブルのcreated_atカラムを更新...")
                # created_atカラムのデフォルト値を日本時間に更新
                connection.execute(text("""
                    ALTER TABLE upload_images 
                    ALTER COLUMN created_at 
                    SET DEFAULT timezone('Asia/Tokyo', now())
                """))
                print("   ✅ created_atカラムのデフォルト値を日本時間に更新しました")
                
                print("3. upload_imagesテーブルのupdated_atカラムを更新...")
                # updated_atカラムのデフォルト値を日本時間に更新
                connection.execute(text("""
                    ALTER TABLE upload_images 
                    ALTER COLUMN updated_at 
                    SET DEFAULT timezone('Asia/Tokyo', now())
                """))
                print("   ✅ updated_atカラムのデフォルト値を日本時間に更新しました")
                
                # 既存のレコードの日時を日本時間に変換（オプション）
                print("4. 既存レコードの日時を確認...")
                result = connection.execute(text("""
                    SELECT COUNT(*) as count 
                    FROM upload_images
                """))
                count = result.scalar()
                print(f"   既存レコード数: {count}")
                
                if count > 0:
                    print("   注意: 既存レコードの日時はUTCのままです。")
                    print("   必要に応じて、既存レコードの日時を日本時間に変換できます。")
                
                # トランザクションコミット
                trans.commit()
                print("\n✅ マイグレーションが正常に完了しました！")
                return True
                
            except Exception as e:
                # エラーが発生した場合はロールバック
                trans.rollback()
                print(f"❌ マイグレーションエラー: {e}")
                return False
                
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False


if __name__ == "__main__":
    if migrate_upload_images_timezone():
        print("\nすべての処理が完了しました！")
    else:
        print("\nマイグレーションに失敗しました。")
        exit(1)

