import sys
import os
from sqlalchemy import text
from app.database.supabase_session import engine
from app.database.supabase_base import SupabaseBase

# 全てのモデルをインポートしてmetadataに登録する
# 1. Core Models
from app.models.users.users import Users
from app.models.child.child import Child
from app.models.story.story_book import StoryBook
from app.models.story.story_plot import StoryPlot
from app.models.story.story_setting import StorySetting
from app.models.credits.credit_ledger import CreditLedger
from app.models.credits.subscription import Subscription
from app.models.iap.app_store_transaction import AppStoreTransaction

# 2. Key Features Models
from app.features._01_image_upload.models.images import UploadImages

def create_tables():
    print("Creating tables in CockroachDB...")
    try:
        # テーブル作成
        SupabaseBase.metadata.create_all(bind=engine)
        print("All tables created successfully!")
        
        # 接続確認用のクエリも実行してみる
        with engine.connect() as conn:
            result = conn.execute(text("SHOW TABLES"))
            print("Current tables:")
            for row in result:
                print(f"- {row[0]}")
                
    except Exception as e:
        print(f"Error creating tables: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_tables()
