import os
import uuid
import base64
from datetime import datetime
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
from app.service.gcs_storage_service import gcs_storage_service

load_dotenv()

class BaseImageGenerator:
    """画像生成の基本機能を提供する基底クラス"""
    
    def __init__(self):
        # APIキーを設定（画像生成用のPaid APIキーを使用）
        api_key = os.getenv("GOOGLE_API_KEY_Paid")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY_Paidが設定されていません")
        
        # APIキーのクリーンアップ（改行、スペース、引用符を削除）
        api_key = api_key.strip().strip('"').strip("'")
        
        # APIキーの形式検証
        if not api_key.startswith("AIza"):
            print(f"⚠️ 警告: APIキーの形式が正しくない可能性があります（AIzaで始まる必要があります）")
        
        # APIキーが空でないことを再確認
        if not api_key or len(api_key) < 20:
            error_msg = f"APIキーが無効です（長さ: {len(api_key)}文字）。APIキーは通常39文字以上です。"
            raise ValueError(error_msg)
        
        try:
            # Gemini クライアントを初期化
            genai.configure(api_key=api_key)
            self.client = genai
            self.model = genai.GenerativeModel('gemini-2.5-flash-image')
        except Exception as e:
            error_msg = f"Gemini APIの初期化に失敗しました: {str(e)}"
            raise ValueError(error_msg) from e
        
        # GCSサービス（グローバルインスタンスを使用）
        self.gcs_service = gcs_storage_service

    def generate_unique_filename(self, prefix: str = "generated_image", extension: str = "png"):
        """ユニークなファイル名を生成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        return f"{prefix}_{timestamp}_{unique_id}.{extension}"

    def save_image_to_storage(self, image_data: bytes, filename: str, user_id: str, story_id: Optional[int] = None, content_type: str = "image/png", page_index: Optional[int] = None) -> Dict[str, Any]:
        """画像をGoogle Cloud Storageに保存（保存前に0.62アスペクト比にクロップリサイズ）"""
        # 保存前にUIのアスペクト比（0.62）に合わせてクロップ＋リサイズ
        from app.utils.image_utils import crop_and_resize_to_aspect_ratio
        image_data = crop_and_resize_to_aspect_ratio(image_data, 1240, 2000)
        
        return self.gcs_service.upload_generated_image(
            file_content=image_data,
            filename=filename,
            user_id=user_id,
            story_id=story_id,
            content_type=content_type,
            page_index=page_index
        )

    def encode_image_to_base64(self, image_path: str) -> str:
        """画像ファイルをBase64エンコード（GCSのURLの場合はGCSクライアントを使用）"""
        try:
            if image_path.startswith("https://") or image_path.startswith("http://"):
                # GCSのURLの場合はGCSクライアントを使用してダウンロード（認証済み）
                if 'storage.googleapis.com' in image_path:
                    # GCSサービスを使用してダウンロード
                    image_data = self.gcs_service.download_file(image_path)
                else:
                    # その他のHTTP/HTTPS URLの場合はrequestsを使用
                    import requests
                    response = requests.get(image_path, timeout=10)
                    response.raise_for_status()
                    content_type = response.headers.get('Content-Type', '')
                    if not content_type.startswith('image/'):
                        raise ValueError(f"画像URLのContent-Typeが不正です: {content_type}")
                    image_data = response.content
            else:
                # ローカルファイルの場合
                with open(image_path, "rb") as image_file:
                    image_data = image_file.read()
            
            # Base64エンコード
            base64_string = base64.b64encode(image_data).decode('utf-8')
            return base64_string
            
        except Exception as e:
            print(f"❌ 画像エンコードエラー: {e}")
            print(f"画像パス: {image_path}")
            raise e
