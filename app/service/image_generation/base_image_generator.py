import os
import uuid
import base64
from datetime import datetime
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
from app.service.gcs_storage_service import GCSStorageService

load_dotenv()

class BaseImageGenerator:
    """画像生成の基本機能を提供する基底クラス"""
    
    def __init__(self):
        # APIキーを設定（画像生成用のPaid APIキーを使用）
        api_key = os.getenv("GOOGLE_API_KEY_Paid") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY_Paid、GEMINI_API_KEYまたはGOOGLE_API_KEYが設定されていません")
        
        # Gemini クライアントを初期化
        genai.configure(api_key=api_key)
        self.client = genai
        self.model = genai.GenerativeModel('gemini-2.5-flash-image-preview')
        
        # GCSサービスを初期化
        try:
            self.gcs_service = GCSStorageService()
        except Exception as e:
            print(f"❌ GCS初期化エラー: {e}")
            raise e

    def generate_unique_filename(self, prefix: str = "generated_image", extension: str = "png"):
        """ユニークなファイル名を生成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        return f"{prefix}_{timestamp}_{unique_id}.{extension}"

    def save_image_to_storage(self, image_data: bytes, filename: str, user_id: str, story_id: Optional[int] = None, content_type: str = "image/png") -> Dict[str, Any]:
        """画像をGoogle Cloud Storageに保存"""
        return self.gcs_service.upload_generated_image(
            file_content=image_data,
            filename=filename,
            user_id=user_id,
            story_id=story_id,
            content_type=content_type
        )

    def encode_image_to_base64(self, image_path: str) -> str:
        """画像ファイルをBase64エンコード"""
        try:
            if image_path.startswith("https://") or image_path.startswith("http://"):
                # GCSのURLの場合は直接ダウンロード（コンテンツタイプ検証とタイムアウト）
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
