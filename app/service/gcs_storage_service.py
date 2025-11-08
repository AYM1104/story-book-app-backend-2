import os
import uuid
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from urllib.parse import unquote
from google.cloud import storage
from google.oauth2 import service_account
from dotenv import load_dotenv
import json
from app.database.supabase_base import get_jst_now

load_dotenv()

class GCSStorageService:
    """Google Cloud Storageを使用して画像を保存・取得するサービス（改善版）"""

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
            print(f"✅ GCS初期化開始")
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
            
            print(f"✅ GCS初期化完了")
        except Exception as e:
            error_msg = (
                f"❌ GCSクライアント初期化エラー: {str(e)}\n"
                f"プロジェクトID: {project_id}\n"
                f"バケット名: {self.bucket_name}"
            )
            raise ValueError(error_msg)

    def generate_unique_filename(self, prefix: str = "uploaded_image", extension: str = "jpg") -> str:
        """ユニークなファイル名を生成（日本時間）"""
        timestamp = get_jst_now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        return f"{prefix}_{timestamp}_{unique_id}.{extension}"

    def _compose_page_filename(self, extension: str, page_index: int) -> str:
        """ページ番号に基づいたファイル名を生成（page_00, page_01, ...）"""
        safe_ext = extension.lower().lstrip('.') if extension else "png"
        return f"page_{page_index:02d}.{safe_ext}"

    def _get_user_path(self, user_id: str, file_type: str = "uploads") -> str:
        """ユーザー別パスを生成（user_id/uploads/yyyy/mm/dd形式、日本時間）"""
        now = get_jst_now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        day = now.strftime("%d")
        return f"{user_id}/{file_type}/{year}/{month}/{day}"

    def upload_image(self, file_content: bytes, filename: str, user_id: str, content_type: str = "image/jpeg") -> Dict[str, Any]:
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
                "timestamp": get_jst_now().isoformat(),
                "user_id": user_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "filename": filename
            }

    def upload_generated_image(self, file_content: bytes, filename: str, user_id: str, story_id: Optional[int] = None, content_type: str = "image/png", page_index: Optional[int] = None) -> Dict[str, Any]:
        """生成された画像をGoogle Cloud Storageにアップロード（改善版）"""
        try:
            # story_idは必須（絵本ごとにフォルダを分けるため）
            if story_id is None:
                return {
                    "success": False,
                    "error": "story_id is required for generated images",
                    "filename": filename
                }
            
            # ページ番号が与えられた場合は命名規約に合わせて上書き
            final_filename = filename
            if page_index is not None:
                ext = filename.split(".")[-1] if "." in filename else "png"
                final_filename = self._compose_page_filename(ext, page_index)

            # ストーリー別パスを生成
            user_path = self._get_user_path(user_id, "generated")
            gcs_path = f"{user_path}/{story_id}/{final_filename}"
            
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
                "filename": final_filename,
                "gcs_path": gcs_path,
                "public_url": public_url,  # storage.googleapis.com形式のURLを使用
                "size_bytes": len(file_content),
                "content_type": content_type,
                "timestamp": get_jst_now().isoformat(),
                "user_id": user_id,
                "story_id": story_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "filename": filename
            }

    def upload_cover_image(self, file_content: bytes, filename: str, user_id: str, story_id: Optional[int] = None, content_type: str = "image/png") -> Dict[str, Any]:
        """表紙画像をGoogle Cloud Storageにアップロード
        
        - story_id は必須: {user_id}/generated/YYYY/MM/DD/{story_id}/page_00.{ext}
        """
        try:
            # story_idは必須（絵本ごとにフォルダを分けるため）
            if story_id is None:
                return {
                    "success": False,
                    "error": "story_id is required for cover images",
                    "filename": filename
                }
            
            user_path = self._get_user_path(user_id, "generated")
            # 表紙は常に page_00.{ext} 命名
            ext = filename.split(".")[-1] if "." in filename else "png"
            cover_filename = self._compose_page_filename(ext, 0)
            gcs_path = f"{user_path}/{story_id}/{cover_filename}"

            blob = self.bucket.blob(gcs_path)
            blob.upload_from_string(
                file_content,
                content_type=content_type
            )

            public_url = f"https://storage.googleapis.com/{self.bucket_name}/{gcs_path}"

            return {
                "success": True,
                "filename": cover_filename,
                "gcs_path": gcs_path,
                "public_url": public_url,
                "size_bytes": len(file_content),
                "content_type": content_type,
                "timestamp": get_jst_now().isoformat(),
                "user_id": user_id,
                "story_id": story_id,
                "is_cover": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "filename": filename
            }

    def delete_user_images(self, user_id: str, file_type: str = "uploads") -> bool:
        """ユーザーの画像を一括削除"""
        try:
            user_path = f"{user_id}/{file_type}"
            blobs = self.bucket.list_blobs(prefix=user_path)
            
            for blob in blobs:
                blob.delete()
            
            return True
        except Exception as e:
            print(f"ユーザー画像削除エラー: {str(e)}")
            return False

    def get_user_images(self, user_id: str, file_type: str = "uploads") -> List[Dict[str, Any]]:
        """ユーザーの画像一覧を取得"""
        try:
            user_path = f"{user_id}/{file_type}"
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

    def delete_file(self, file_path: str) -> Dict[str, Any]:
        """指定されたファイルパスのGCS上のファイルを削除
        
        Args:
            file_path: GCS上のファイルパス（例: user_id/uploads/2024/01/01/filename.jpg）
            
        Returns:
            Dict[str, Any]: 削除結果
                - success: bool - 削除成功かどうか
                - error: str - エラーメッセージ（失敗時）
        """
        try:
            # URL形式の場合はパスを抽出
            if file_path.startswith('http'):
                # storage.googleapis.com形式のURLからパスを抽出
                if 'storage.googleapis.com' in file_path:
                    # https://storage.googleapis.com/bucket_name/path/to/file から path/to/file を抽出
                    parts = file_path.split('/')
                    bucket_index = parts.index(self.bucket_name) if self.bucket_name in parts else -1
                    if bucket_index >= 0 and bucket_index < len(parts) - 1:
                        file_path = '/'.join(parts[bucket_index + 1:])
                    else:
                        return {
                            "success": False,
                            "error": f"無効なURL形式です: {file_path}"
                        }
                else:
                    return {
                        "success": False,
                        "error": f"サポートされていないURL形式です: {file_path}"
                    }
            
            # ファイルを削除
            blob = self.bucket.blob(file_path)
            if blob.exists():
                blob.delete()
                print(f"✅ GCSファイル削除成功: {file_path}")
                return {
                    "success": True,
                    "file_path": file_path
                }
            else:
                print(f"⚠️ GCSファイルが存在しません: {file_path}")
                return {
                    "success": False,
                    "error": f"ファイルが存在しません: {file_path}"
                }
        except Exception as e:
            print(f"❌ GCSファイル削除エラー: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def generate_signed_url(self, file_path_or_url: str, expiration_hours: int = 1) -> str:
        """GCSファイルの署名付きURLを生成
        
        Args:
            file_path_or_url: GCS上のファイルパスまたはURL
            expiration_hours: URLの有効期限（時間単位、デフォルト1時間）
            
        Returns:
            str: 署名付きURL
        """
        try:
            # URL形式の場合はパスを抽出
            file_path = file_path_or_url
            if file_path_or_url.startswith('http'):
                # storage.googleapis.com形式のURLからパスを抽出
                if 'storage.googleapis.com' in file_path_or_url:
                    # クエリパラメータを除去
                    url_without_query = file_path_or_url.split('?')[0]
                    # https://storage.googleapis.com/bucket_name/path/to/file から path/to/file を抽出
                    parts = url_without_query.split('/')
                    bucket_index = parts.index(self.bucket_name) if self.bucket_name in parts else -1
                    if bucket_index >= 0 and bucket_index < len(parts) - 1:
                        # URLエンコードされた文字をデコード（例: %7C -> |）
                        file_path = '/'.join(parts[bucket_index + 1:])
                        file_path = unquote(file_path)
                    else:
                        raise ValueError(f"無効なURL形式です: {file_path_or_url}")
                else:
                    raise ValueError(f"サポートされていないURL形式です: {file_path_or_url}")
            
            # 署名付きURLを生成
            blob = self.bucket.blob(file_path)
            if not blob.exists():
                raise ValueError(f"ファイルが存在しません: {file_path}")
            
            signed_url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(hours=expiration_hours),
                method="GET"
            )
            
            print(f"✅ 署名付きURL生成成功: {file_path}")
            return signed_url
            
        except Exception as e:
            print(f"❌ 署名付きURL生成エラー: {str(e)}")
            raise e

    def download_file(self, file_path_or_url: str) -> bytes:
        """GCSからファイルをダウンロード（URLまたはパス形式に対応）
        
        Args:
            file_path_or_url: GCS上のファイルパスまたはURL
            
        Returns:
            bytes: ファイルのバイトデータ
            
        Raises:
            ValueError: ファイルが見つからない場合
            Exception: ダウンロードエラー
        """
        try:
            # URL形式の場合はパスを抽出
            file_path = file_path_or_url
            if file_path_or_url.startswith('http'):
                # storage.googleapis.com形式のURLからパスを抽出
                if 'storage.googleapis.com' in file_path_or_url:
                    # クエリパラメータを除去
                    url_without_query = file_path_or_url.split('?')[0]
                    # https://storage.googleapis.com/bucket_name/path/to/file から path/to/file を抽出
                    parts = url_without_query.split('/')
                    bucket_index = parts.index(self.bucket_name) if self.bucket_name in parts else -1
                    if bucket_index >= 0 and bucket_index < len(parts) - 1:
                        # URLエンコードされた文字をデコード（例: %7C -> |）
                        file_path = '/'.join(parts[bucket_index + 1:])
                        file_path = unquote(file_path)
                    else:
                        raise ValueError(f"無効なURL形式です: {file_path_or_url}")
                else:
                    raise ValueError(f"サポートされていないURL形式です: {file_path_or_url}")
            
            # GCSからファイルをダウンロード
            blob = self.bucket.blob(file_path)
            if not blob.exists():
                raise ValueError(f"ファイルが存在しません: {file_path}")
            
            file_data = blob.download_as_bytes()
            print(f"✅ GCSファイルダウンロード成功: {file_path} ({len(file_data)} bytes)")
            return file_data
            
        except Exception as e:
            print(f"❌ GCSファイルダウンロードエラー: {str(e)}")
            raise e


# グローバルインスタンス（シングルトンパターン的な使用）
gcs_storage_service = GCSStorageService()