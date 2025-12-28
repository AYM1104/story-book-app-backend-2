"""
シンプルな画像アップロードテスト
エラーの詳細を確認するため
"""
import requests
from pathlib import Path
import sys

if len(sys.argv) < 2:
    print("使用方法: python test_upload_simple.py <画像ファイルのパス>")
    sys.exit(1)

image_path = sys.argv[1]

if not Path(image_path).exists():
    print(f"❌ ファイルが見つかりません: {image_path}")
    sys.exit(1)

filename = Path(image_path).name
ext = Path(image_path).suffix.lower()
content_type_map = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.webp': 'image/webp'
}
content_type = content_type_map.get(ext, 'image/png')

print("="*60)
print("画像アップロードテスト")
print("="*60)
print(f"ファイル: {filename}")
print(f"パス: {image_path}")
print(f"拡張子: {ext}")
print(f"Content-Type: {content_type}")
print(f"ファイルサイズ: {Path(image_path).stat().st_size / 1024:.2f} KB")
print()

try:
    with open(image_path, 'rb') as f:
        files = {'file': (filename, f, content_type)}
        data = {'user_id': 'test|123456789'}
        
        print("アップロード中...")
        response = requests.post(
            'http://localhost:8000/api/images/upload',
            files=files,
            data=data,
            timeout=120
        )
        
        print(f"\nステータスコード: {response.status_code}")
        print(f"レスポンスヘッダー:")
        for key, value in response.headers.items():
            if key.lower() in ['content-type', 'content-length']:
                print(f"  {key}: {value}")
        
        print(f"\nレスポンス本文:")
        print(response.text)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ 成功!")
            print(f"upload_image_id: {result.get('id')}")
            print(f"public_url: {result.get('public_url', 'N/A')}")
        else:
            print(f"\n❌ エラーが発生しました")
            try:
                error_json = response.json()
                print(f"\nエラー詳細:")
                import json
                print(json.dumps(error_json, indent=2, ensure_ascii=False))
            except:
                pass
            
            print(f"\n💡 バックエンドサーバーのログを確認してください")
            print(f"   サーバーを起動しているターミナルでエラーメッセージを探してください")
            
except requests.exceptions.ConnectionError:
    print("❌ バックエンドサーバーに接続できません")
    print("   バックエンドサーバーが起動しているか確認してください")
    print("   cd backend/backend && ./venv/bin/uvicorn app.main:app --reload")
except requests.exceptions.Timeout:
    print("❌ リクエストがタイムアウトしました")
    print("   処理に時間がかかりすぎています")
except Exception as e:
    print(f"❌ 予期しないエラー: {e}")
    import traceback
    traceback.print_exc()

