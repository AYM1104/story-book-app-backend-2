"""
GCSバケットの存在確認と一覧表示
"""
import os
from google.cloud import storage
from google.oauth2 import service_account
from dotenv import load_dotenv

load_dotenv()

# 環境変数から取得
bucket_name = os.getenv("GCS_BUCKET_NAME")
project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

print("="*60)
print("GCSバケット確認")
print("="*60)
print(f"設定されているバケット名: {bucket_name}")
print(f"プロジェクトID: {project_id}")
print(f"認証情報ファイル: {credentials_path}")
print()

if not bucket_name:
    print("❌ GCS_BUCKET_NAMEが設定されていません")
    exit(1)

if not credentials_path or not os.path.exists(credentials_path):
    print("❌ GOOGLE_APPLICATION_CREDENTIALSが設定されていないか、ファイルが存在しません")
    exit(1)

try:
    # GCSクライアントを初期化
    if credentials_path and os.path.exists(credentials_path):
        credentials = service_account.Credentials.from_service_account_file(credentials_path)
        if project_id:
            client = storage.Client(credentials=credentials, project=project_id)
        else:
            client = storage.Client(credentials=credentials)
    else:
        if project_id:
            client = storage.Client(project=project_id)
        else:
            client = storage.Client()
    
    # バケットの存在確認
    print("バケットの存在確認中...")
    try:
        bucket = client.bucket(bucket_name)
        if bucket.exists():
            print(f"✅ バケット '{bucket_name}' は存在します")
            print(f"   ロケーション: {bucket.location}")
            print(f"   ストレージクラス: {bucket.storage_class}")
        else:
            print(f"❌ バケット '{bucket_name}' は存在しません")
            print()
            print("利用可能なバケット一覧:")
            print("-" * 60)
            buckets = list(client.list_buckets())
            if buckets:
                for b in buckets:
                    print(f"  - {b.name}")
                    if 'ehonnotane' in b.name.lower() or 'image' in b.name.lower():
                        print(f"    ⭐ このバケットが目的のものかもしれません")
            else:
                print("  （バケットが見つかりませんでした）")
    except Exception as e:
        print(f"❌ バケット確認エラー: {e}")
        print()
        print("利用可能なバケット一覧:")
        print("-" * 60)
        try:
            buckets = list(client.list_buckets())
            if buckets:
                for b in buckets:
                    print(f"  - {b.name}")
                    if 'ehonnotane' in b.name.lower() or 'image' in b.name.lower():
                        print(f"    ⭐ このバケットが目的のものかもしれません")
            else:
                print("  （バケットが見つかりませんでした）")
        except Exception as list_error:
            print(f"  バケット一覧の取得に失敗しました: {list_error}")
    
except Exception as e:
    print(f"❌ GCSクライアント初期化エラー: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*60)
print("💡 バケット名を修正するには:")
print("   .envファイルの GCS_BUCKET_NAME を正しいバケット名に変更してください")
print("="*60)

