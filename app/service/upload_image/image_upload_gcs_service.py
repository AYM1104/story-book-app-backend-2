"""
画像アップロード用GCSサービス
"""
import os
import uuid
import time
import re
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
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        # 必須環境変数のチェック
        missing_vars = []
        if not self.bucket_name:
            missing_vars.append("GCS_BUCKET_NAME")
        
        if missing_vars:
            error_msg = (
                f"❌ GCS初期化エラー: 以下の環境変数が設定されていません: {', '.join(missing_vars)}\n"
                f"設定方法:\n"
                f"  export GCS_BUCKET_NAME=your-bucket-name"
            )
            raise ValueError(error_msg)
        
        # バケット名の検証（GCSの命名規則に準拠）
        self.bucket_name = self.bucket_name.strip() if self.bucket_name else ""
        if not self.bucket_name:
            raise ValueError(
                "❌ GCS初期化エラー: GCS_BUCKET_NAMEが空です。\n"
                "設定方法: export GCS_BUCKET_NAME=your-bucket-name"
            )
        
        # GCSバケット名の命名規則チェック
        # - 3〜63文字の長さ
        # - 小文字、数字、ハイフン（-）のみ使用可能
        # - 数字または文字で始まり、数字または文字で終わる必要がある
        # - 連続するハイフンは使用できない
        bucket_name_errors = []
        
        if len(self.bucket_name) < 3 or len(self.bucket_name) > 63:
            bucket_name_errors.append(f"バケット名の長さは3〜63文字である必要があります（現在: {len(self.bucket_name)}文字）")
        
        if not (self.bucket_name[0].isalnum() and self.bucket_name[-1].isalnum()):
            bucket_name_errors.append(
                f"バケット名は数字または文字で始まり、数字または文字で終わる必要があります（現在: '{self.bucket_name[0]}'で始まり、'{self.bucket_name[-1]}'で終わる）"
            )
        
        # 使用可能な文字のチェック（小文字、数字、ハイフンのみ）
        if not re.match(r'^[a-z0-9-]+$', self.bucket_name):
            bucket_name_errors.append("バケット名は小文字、数字、ハイフン（-）のみ使用可能です")
        
        # 連続するハイフンのチェック
        if '--' in self.bucket_name:
            bucket_name_errors.append("バケット名に連続するハイフン（--）は使用できません")
        
        if bucket_name_errors:
            error_msg = (
                f"❌ GCSバケット名の検証エラー:\n"
                f"バケット名: '{self.bucket_name}'\n"
                f"問題点:\n" + "\n".join(f"  - {err}" for err in bucket_name_errors) + "\n"
                f"GCSバケット名の命名規則:\n"
                f"  - 3〜63文字の長さ\n"
                f"  - 小文字、数字、ハイフン（-）のみ使用可能\n"
                f"  - 数字または文字で始まり、数字または文字で終わる必要がある\n"
                f"  - 連続するハイフンは使用できない"
            )
            raise ValueError(error_msg)
        
        # GCSクライアント初期化（ADCフォールバック対応）
        try:
            print(f"✅ ImageUploadGCS初期化開始")
            print(f"  - プロジェクトID: {project_id}")
            print(f"  - バケット名: {self.bucket_name}")
            
            # Service Account認証ファイルが存在する場合はそれを使用、なければADC（Cloud Run等で自動認証）
            if credentials_path and os.path.exists(credentials_path):
                print(f"  - Service Account認証を使用: {credentials_path}")
                credentials = service_account.Credentials.from_service_account_file(credentials_path)
                if project_id:
                    self.client = storage.Client(credentials=credentials, project=project_id)
                else:
                    self.client = storage.Client(credentials=credentials)
            else:
                print(f"  - ADC（Application Default Credentials）を使用")
                if project_id:
                    self.client = storage.Client(project=project_id)
                else:
                    self.client = storage.Client()
            
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
        """ユーザー別パスを生成（user_id/uploads/yyyy/mm/dd形式）"""
        now = datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        day = now.strftime("%d")
        return f"{user_id}/{file_type}/{year}/{month}/{day}"

    async def upload_image(
        self, 
        file_content: bytes, 
        filename: str, 
        user_id: str, 
        content_type: str = "image/jpeg"
    ) -> Dict[str, Any]:
        """画像をGoogle Cloud Storageにアップロード"""
        start_time = time.time()
        
        # print("=== GCSアップロード処理開始 ===")
        
        try:
            # ファイル名を生成
            file_extension = filename.split(".")[-1].lower() if "." in filename else "jpg"
            unique_filename = self.generate_unique_filename("uploaded_image", file_extension)
            
            # ユーザー別パスを生成
            user_path = self._get_user_path(user_id, "uploads")
            gcs_path = f"{user_path}/{unique_filename}"
            
            # print(f"⭐️ アップロード先パス: {gcs_path}")
            
            # ファイルをアップロード
            blob = self.bucket.blob(gcs_path)
            blob.upload_from_string(
                file_content,
                content_type=content_type
            )
            
            # storage.googleapis.com形式のURLを生成
            public_url = f"https://storage.googleapis.com/{self.bucket_name}/{gcs_path}"
            
            processing_time = time.time() - start_time
            print(f"　⭐️ GCSアップロード時間: {processing_time:.3f}秒")
            print(f"　⭐️ ファイルパス: {gcs_path}")
            print(f"　⭐️ GCS public_url: {public_url}")
            # print("=== GCSアップロード処理完了 ===")
            
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
            print(f"❌ GCSアップロード時間（エラー）: {processing_time:.3f}秒")
            print(f"❌ GCSエラー: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "filename": filename,
                "processing_time": processing_time
            }


# サービスインスタンス
image_upload_gcs_service = ImageUploadGCSService()
