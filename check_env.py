"""
環境変数の設定状況を確認するスクリプト
"""
import os
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

print("="*60)
print("環境変数の設定状況を確認します")
print("="*60)

# 必須環境変数のリスト
required_vars = {
    "SUPABASE_DB_URL": "Supabaseデータベース接続URL",
    "GCS_BUCKET_NAME": "Google Cloud Storageバケット名",
    "GOOGLE_APPLICATION_CREDENTIALS": "GCS認証情報ファイルパス",
    "ENABLE_TEST_MODE": "テストモード（オプション）",
}

# 推奨環境変数のリスト
recommended_vars = {
    "GOOGLE_CLOUD_PROJECT": "Google Cloud プロジェクトID",
    "GEMINI_API_KEY": "Gemini APIキー",
    "GOOGLE_API_KEY_Free": "Google APIキー（無料プラン）",
    "GOOGLE_API_KEY_Paid": "Google APIキー（有料プラン）",
}

print("\n【必須環境変数】")
all_ok = True
for var_name, description in required_vars.items():
    value = os.getenv(var_name)
    if value:
        # 機密情報は一部のみ表示
        if "CREDENTIALS" in var_name or "URL" in var_name or "KEY" in var_name:
            display_value = value[:20] + "..." if len(value) > 20 else value
        else:
            display_value = value
        print(f"  ✅ {var_name}: {display_value}")
    else:
        print(f"  ❌ {var_name}: 未設定 ({description})")
        if var_name != "ENABLE_TEST_MODE":
            all_ok = False

print("\n【推奨環境変数】")
for var_name, description in recommended_vars.items():
    value = os.getenv(var_name)
    if value:
        if "KEY" in var_name:
            display_value = value[:20] + "..." if len(value) > 20 else value
        else:
            display_value = value
        print(f"  ✅ {var_name}: {display_value}")
    else:
        print(f"  ⚠️  {var_name}: 未設定 ({description})")

print("\n" + "="*60)
if all_ok:
    print("✅ 必須環境変数はすべて設定されています")
else:
    print("❌ 一部の必須環境変数が設定されていません")
    print("\n.envファイルに以下を追加してください:")
    print("  SUPABASE_DB_URL=postgresql://...")
    print("  GCS_BUCKET_NAME=your-bucket-name")
    print("  GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json")
print("="*60)

