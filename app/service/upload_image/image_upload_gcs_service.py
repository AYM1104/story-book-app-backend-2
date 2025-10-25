"""
画像アップロード用GCSサービス
"""
import os
import uuid
import time
from datetime import datetime
from typing import Dict, Any
from google.cloud import storage
from google.oauth2 import service_account
from dotenv import load_dotenv

load_dotenv()


class ImageUploadGCSService:
    """画像アップロード専用のGCSサービス"""

    def __init__(self):
        # 環境変数チェック
        self.bucket_name = os.getenv("GCS_BUCKET_NAME")
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        
        # 必須環境変数のチェック
        missing_vars = []
        if not self.bucket_name:
            missing_vars.append("GCS_BUCKET_NAME")
        if not project_id:
            missing_vars.append("GOOGLE_CLOUD_PROJECT")
        
        if missing_vars:
            error_msg = (
                f"❌ GCS初期化エラー: 以下の環境変数が設定されていません: {', '.join(missing_vars)}\n"
                f"設定方法:\n"
                f"  export GCS_BUCKET_NAME=your-bucket-name\n"
                f"  export GOOGLE_CLOUD_PROJECT=your-project-id"
            )
            raise ValueError(error_msg)
        
        # GCSクライアント初期化
        try:
            print(f"✅ ImageUploadGCS初期化開始")
            print(f"  - プロジェクトID: {project_id}")
            print(f"  - バケット名: {self.bucket_name}")
            
            self.client = storage.Client(project=project_id)
            self.bucket = self.client.bucket(self.bucket_name)
            
            print(f"✅ ImageUploadGCS初期化完了")
        except Exception as e:
            error_msg = (
                f"❌ GCSクライアント初期化エラー: {str(e)}\n"
                f"プロジェクトID: {project_id}\n"
                f"バケット名: {self.bucket_name}"
            )
            raise ValueError(error_msg)

    def generate_unique_filename(self, prefix: str = "uploaded_image", extension: str = "jpg") -> str:
        """ユニークなファイル名を生成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        return f"{prefix}_{timestamp}_{unique_id}.{extension}"

    def _get_user_path(self, user_id: str, file_type: str = "uploads") -> str:
        """ユーザー別パスを生成"""
        now = datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        return f"users/{user_id}/{file_type}/{year}/{month}"

    async def upload_image(
        self, 
        file_content: bytes, 
        filename: str, 
        user_id: str, 
        content_type: str = "image/jpeg"
    ) -> Dict[str, Any]:
        """画像をGoogle Cloud Storageにアップロード"""
        start_time = time.time()
        
        print("=== GCSアップロード処理開始 ===")
        
        try:
            # ファイル名を生成
            file_extension = filename.split(".")[-1].lower() if "." in filename else "jpg"
            unique_filename = self.generate_unique_filename("uploaded_image", file_extension)
            
            # ユーザー別パスを生成
            user_path = self._get_user_path(user_id, "uploads")
            gcs_path = f"{user_path}/{unique_filename}"
            
            print(f"アップロード先パス: {gcs_path}")
            
            # ファイルをアップロード
            blob = self.bucket.blob(gcs_path)
            blob.upload_from_string(
                file_content,
                content_type=content_type
            )
            
            # storage.googleapis.com形式のURLを生成
            public_url = f"https://storage.googleapis.com/{self.bucket_name}/{gcs_path}"
            
            processing_time = time.time() - start_time
            print(f"⏱️ GCSアップロード時間: {processing_time:.3f}秒")
            print(f"ファイルパス: {gcs_path}")
            print(f"GCS public_url: {public_url}")
            print("=== GCSアップロード処理完了 ===")
            
            return {
                "success": True,
                "filename": unique_filename,
                "gcs_path": gcs_path,
                "public_url": public_url,
                "size_bytes": len(file_content),
                "content_type": content_type,
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "processing_time": processing_time
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            print(f"⏱️ GCSアップロード時間（エラー）: {processing_time:.3f}秒")
            print(f"GCSエラー: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "filename": filename,
                "processing_time": processing_time
            }


# サービスインスタンス
image_upload_gcs_service = ImageUploadGCSService()
