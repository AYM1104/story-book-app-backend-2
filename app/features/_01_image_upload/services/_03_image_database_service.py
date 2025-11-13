"""
画像データベース保存サービス
"""
import time
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.features._01_image_upload.models.images import UploadImages


class ImageDatabaseService:
    """画像データベース保存処理を担当するサービス"""
    
    async def save_image_to_database(
        self,
        db: Session,
        file_name: Optional[str],
        file_path: str,
        content_type: str,
        size_bytes: int,
        user_id: str,
        meta_data_json: Optional[str],
        public_url: str
    ) -> Dict[str, Any]:
        """
        画像情報をデータベースに保存する
        
        Args:
            db: データベースセッション
            file_name: ファイル名
            file_path: ファイルパス
            content_type: コンテンツタイプ
            size_bytes: ファイルサイズ
            user_id: ユーザーID
            meta_data_json: メタデータ（JSON文字列）
            public_url: パブリックURL
        
        Returns:
            保存結果の辞書
        """
        start_time = time.time()
        
        print("=== データベース保存処理開始 ===")
        
        try:
            # 画像レコードを作成
            new_image = UploadImages(
                file_name=file_name,
                file_path=file_path,
                content_type=content_type,
                size_bytes=size_bytes,
                user_id=user_id,
                meta_data=meta_data_json,
                public_url=public_url,
            )
            
            # データベースに保存
            db.add(new_image)
            db.commit()
            db.refresh(new_image)
            
            processing_time = time.time() - start_time
            print(f"⏱️ データベース保存時間: {processing_time:.3f}秒")
            print(f"保存された画像のmeta_data: {new_image.meta_data}")
            print("=== データベース保存処理完了 ===")
            
            # レスポンスデータを準備
            response_data = {
                "id": new_image.id,
                "file_name": new_image.file_name,
                "file_path": new_image.file_path,
                "content_type": new_image.content_type,
                "size_bytes": new_image.size_bytes,
                "user_id": new_image.user_id,  # 文字列型のuser_id
                "uploaded_at": new_image.created_at.isoformat(),  # ISO文字列に変換
                "meta_data": new_image.meta_data,
                "public_url": new_image.public_url,
            }
            
            return {
                "success": True,
                "image_record": new_image,
                "response_data": response_data,
                "processing_time": processing_time
            }
            
        except Exception as error:
            db.rollback()
            processing_time = time.time() - start_time
            print(f"⏱️ データベース保存時間（エラー）: {processing_time:.3f}秒")
            print(f"データベース保存エラー: {error}")
            
            return {
                "success": False,
                "error": str(error),
                "processing_time": processing_time
            }


# サービスインスタンス
image_database_service = ImageDatabaseService()
