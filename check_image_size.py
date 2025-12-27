"""
画像のサイズを確認するスクリプト
"""
from PIL import Image
import io
import requests
from urllib.parse import unquote
from app.service.gcs_storage_service import gcs_storage_service

def check_image_size(image_url: str):
    """
    画像URLから画像を取得してサイズを確認する
    
    Args:
        image_url: 画像のURL
    """
    try:
        print(f"画像URL: {image_url[:100]}...")  # URLが長いので最初の100文字だけ表示
        print("画像を取得中...")
        
        image_data = None
        
        # apidata.googleusercontent.com形式のURL（直接ダウンロード用）
        if 'apidata.googleusercontent.com' in image_url:
            print("直接ダウンロードURLとして処理します...")
            response = requests.get(image_url, timeout=30)
            if response.status_code == 200:
                image_data = response.content
                print(f"✅ 画像データ取得成功: {len(image_data)} bytes")
            else:
                print(f"❌ HTTPエラー: ステータスコード {response.status_code}")
                return
        # storage.cloud.google.com形式をstorage.googleapis.com形式に変換
        elif 'storage.cloud.google.com' in image_url:
            image_url = image_url.replace('storage.cloud.google.com', 'storage.googleapis.com')
            print(f"URL変換後: {image_url}")
            image_data = gcs_storage_service.download_file(image_url)
            print(f"✅ 画像データ取得成功: {len(image_data)} bytes")
        else:
            # その他のURL形式はGCSサービス経由で取得を試みる
            image_data = gcs_storage_service.download_file(image_url)
            print(f"✅ 画像データ取得成功: {len(image_data)} bytes")
        
        # PILで画像を開く
        image = Image.open(io.BytesIO(image_data))
        
        # 画像情報を表示
        print("\n=== 画像情報 ===")
        print(f"幅 (width): {image.width} px")
        print(f"高さ (height): {image.height} px")
        print(f"アスペクト比: {image.width / image.height:.2f}")
        print(f"形式: {image.format}")
        print(f"モード: {image.mode}")
        print(f"ファイルサイズ: {len(image_data)} bytes ({len(image_data) / 1024:.2f} KB)")
        
        # 期待されるサイズと比較
        expected_width = 1280
        expected_height = 1920
        
        print("\n=== サイズ確認 ===")
        if image.width == expected_width and image.height == expected_height:
            print(f"✅ 画像サイズは {expected_width}×{expected_height} です！")
        else:
            print(f"⚠️ 画像サイズは {image.width}×{image.height} です")
            print(f"   期待されるサイズ: {expected_width}×{expected_height}")
            print(f"   幅の差: {abs(image.width - expected_width)} px")
            print(f"   高さの差: {abs(image.height - expected_height)} px")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 確認したい画像URL
    image_url = "https://storage.cloud.google.com/ehonnotane-images-storage/google-oauth2%7C104323599082993871312/uploads/2025/12/25/uploaded_image_20251225_155139_d647fe16.jpg"
    
    check_image_size(image_url)

