import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from google.cloud import storage
from google.oauth2 import service_account
from dotenv import load_dotenv
import json

load_dotenv()

class GCSStorageService:
    """Google Cloud Storageを使用して画像を保存・取得するサービス（改善版）"""

    def __init__(self):
        self.bucket_name = os.getenv("GCS_BUCKET_NAME")
        
        if not self.bucket_name:
            raise ValueError("GCS_BUCKET_NAMEが設定されていません")
        
        # Cloud Run環境ではサービスアカウントのメタデータ認証を使用
        # 明示的な認証情報設定は不要
        print("✅ GCS認証: Cloud Runサービスアカウントを使用")
        self.client = storage.Client()
        self.bucket = self.client.bucket(self.bucket_name)

    def generate_unique_filename(self, prefix: str = "uploaded_image", extension: str = "jpg") -> str:
        """ユニークなファイル名を生成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        return f"{prefix}_{timestamp}_{unique_id}.{extension}"

    def _get_user_path(self, user_id: int, file_type: str = "uploads") -> str:
        """ユーザー別パスを生成"""
        now = datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        return f"users/{user_id}/{file_type}/{year}/{month}"

    def upload_image(self, file_content: bytes, filename: str, user_id: int, content_type: str = "image/jpeg") -> Dict[str, Any]:
        """画像をGoogle Cloud Storageにアップロード（改善版）"""
        try:
            # ファイル名を生成
            file_extension = filename.split(".")[-1].lower() if "." in filename else "jpg"
            unique_filename = self.generate_unique_filename("uploaded_image", file_extension)
            
            # ユーザー別パスを生成
            user_path = self._get_user_path(user_id, "uploads")
            gcs_path = f"{user_path}/{unique_filename}"
            
            # ファイルをアップロード
            blob = self.bucket.blob(gcs_path)
            blob.upload_from_string(
                file_content,
                content_type=content_type
            )
            
            # storage.googleapis.com形式のURLを生成（正しいGCSの公開URL形式）
            public_url = f"https://storage.googleapis.com/{self.bucket_name}/{gcs_path}"
            
            return {
                "success": True,
                "filename": unique_filename,
                "gcs_path": gcs_path,
                "public_url": public_url,  # storage.googleapis.com形式のURLを使用
                "size_bytes": len(file_content),
                "content_type": content_type,
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "filename": filename
            }

    def upload_generated_image(self, file_content: bytes, filename: str, user_id: int, story_id: Optional[int] = None, content_type: str = "image/png") -> Dict[str, Any]:
        """生成された画像をGoogle Cloud Storageにアップロード（改善版）"""
        try:
            # ストーリー別パスを生成
            if story_id:
                user_path = self._get_user_path(user_id, "generated")
                gcs_path = f"{user_path}/{story_id}/pages/{filename}"
            else:
                user_path = self._get_user_path(user_id, "generated")
                gcs_path = f"{user_path}/temp/{filename}"
            
            # ファイルをアップロード
            blob = self.bucket.blob(gcs_path)
            blob.upload_from_string(
                file_content,
                content_type=content_type
            )
            
            # storage.googleapis.com形式のURLを生成（正しいGCSの公開URL形式）
            public_url = f"https://storage.googleapis.com/{self.bucket_name}/{gcs_path}"
            
            return {
                "success": True,
                "filename": filename,
                "gcs_path": gcs_path,
                "public_url": public_url,  # storage.googleapis.com形式のURLを使用
                "size_bytes": len(file_content),
                "content_type": content_type,
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "story_id": story_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "filename": filename
            }

    def delete_user_images(self, user_id: int, file_type: str = "uploads") -> bool:
        """ユーザーの画像を一括削除"""
        try:
            user_path = f"users/{user_id}/{file_type}"
            blobs = self.bucket.list_blobs(prefix=user_path)
            
            for blob in blobs:
                blob.delete()
            
            return True
        except Exception as e:
            print(f"ユーザー画像削除エラー: {str(e)}")
            return False

    def get_user_images(self, user_id: int, file_type: str = "uploads") -> List[Dict[str, Any]]:
        """ユーザーの画像一覧を取得"""
        try:
            user_path = f"users/{user_id}/{file_type}"
            blobs = self.bucket.list_blobs(prefix=user_path)
            
            images = []
            for blob in blobs:
                # 認証済みURLを生成
                signed_url = blob.generate_signed_url(
                    version="v4",
                    expiration=timedelta(hours=1),
                    method="GET"
                )
                
                images.append({
                    "name": blob.name,
                    "size": blob.size,
                    "created": blob.time_created.isoformat(),
                    "public_url": signed_url
                })
            
            return images
        except Exception as e:
            print(f"ユーザー画像取得エラー: {str(e)}")
            return []

    def get_public_url(self, file_path: str) -> str:
        """ファイルパスからGCSのstorage.googleapis.com形式URLを生成"""
        try:
            # ファイルパスが既にURLの場合はそのまま返す
            if file_path.startswith('http'):
                # 既存のURLをそのまま返す（storage.googleapis.com形式を維持）
                return file_path
            
            # storage.googleapis.com形式のURLを生成
            public_url = f"https://storage.googleapis.com/{self.bucket_name}/{file_path}"
            return public_url
        except Exception as e:
            print(f"公開URL生成エラー: {str(e)}")
            return file_path